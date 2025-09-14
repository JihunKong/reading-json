#!/usr/bin/env python3
"""
Student Tracker Module
Individual student progress tracking and personalized learning path generation
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
import pandas as pd
import numpy as np
from collections import defaultdict
import pickle


@dataclass
class StudentProfile:
    """Complete student profile with learning history"""
    student_id: str
    name: str
    email: str
    class_id: str
    created_at: datetime
    last_active: datetime
    total_sessions: int = 0
    total_time_spent: float = 0  # in minutes
    preferred_difficulty: str = "medium"
    learning_style: str = "balanced"
    current_streak: int = 0
    longest_streak: int = 0
    achievements: List[str] = field(default_factory=list)
    skill_levels: Dict[str, float] = field(default_factory=dict)
    learning_goals: List[Dict] = field(default_factory=list)
    
    def to_dict(self):
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['last_active'] = self.last_active.isoformat()
        return data


@dataclass
class LearningSession:
    """Individual learning session data"""
    session_id: str
    student_id: str
    start_time: datetime
    end_time: Optional[datetime]
    tasks_attempted: List[str]
    tasks_completed: List[str]
    accuracy: float
    avg_response_time: float
    focus_score: float  # Based on consistency of responses
    notes: str = ""
    
    def duration_minutes(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 60
        return 0


@dataclass
class SkillAssessment:
    """Assessment of specific reading skills"""
    skill_name: str
    current_level: float  # 0-100
    trend: str  # "improving", "stable", "declining"
    last_assessed: datetime
    assessment_count: int
    recommendations: List[str]
    
    def needs_practice(self) -> bool:
        return self.current_level < 70 or self.trend == "declining"


class StudentTracker:
    """Track individual student progress and generate personalized learning paths"""
    
    def __init__(self, data_dir: str = "./student_data"):
        self.data_dir = data_dir
        self.ensure_directories()
        self.profiles: Dict[str, StudentProfile] = {}
        self.sessions: Dict[str, List[LearningSession]] = defaultdict(list)
        self.skill_assessments: Dict[str, Dict[str, SkillAssessment]] = defaultdict(dict)
        self.load_existing_data()
        
    def ensure_directories(self):
        """Create necessary directories"""
        dirs = [
            self.data_dir,
            os.path.join(self.data_dir, "profiles"),
            os.path.join(self.data_dir, "sessions"),
            os.path.join(self.data_dir, "assessments"),
            os.path.join(self.data_dir, "learning_paths"),
            os.path.join(self.data_dir, "progress_reports")
        ]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    def load_existing_data(self):
        """Load existing student data from storage"""
        # Load profiles
        profile_dir = os.path.join(self.data_dir, "profiles")
        for filename in os.listdir(profile_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(profile_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        student_id = data['student_id']
                        self.profiles[student_id] = self._dict_to_profile(data)
                except Exception as e:
                    print(f"Error loading profile {filename}: {e}")
    
    def _dict_to_profile(self, data: Dict) -> StudentProfile:
        """Convert dictionary to StudentProfile"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_active'] = datetime.fromisoformat(data['last_active'])
        return StudentProfile(**data)
    
    def create_student_profile(self,
                              student_id: str,
                              name: str,
                              email: str,
                              class_id: str) -> StudentProfile:
        """Create a new student profile"""
        profile = StudentProfile(
            student_id=student_id,
            name=name,
            email=email,
            class_id=class_id,
            created_at=datetime.now(),
            last_active=datetime.now(),
            skill_levels={
                'keyword_identification': 50.0,
                'center_sentence': 50.0,
                'center_paragraph': 50.0,
                'topic_comprehension': 50.0,
                'vocabulary': 50.0,
                'inference': 50.0,
                'summary': 50.0
            }
        )
        
        self.profiles[student_id] = profile
        self.save_profile(profile)
        return profile
    
    def save_profile(self, profile: StudentProfile):
        """Save student profile to disk"""
        filepath = os.path.join(self.data_dir, "profiles", f"{profile.student_id}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(profile.to_dict(), f, ensure_ascii=False, indent=2)
    
    def start_learning_session(self, student_id: str) -> LearningSession:
        """Start a new learning session"""
        session = LearningSession(
            session_id=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{student_id}",
            student_id=student_id,
            start_time=datetime.now(),
            end_time=None,
            tasks_attempted=[],
            tasks_completed=[],
            accuracy=0.0,
            avg_response_time=0.0,
            focus_score=1.0
        )
        
        self.sessions[student_id].append(session)
        
        # Update profile
        if student_id in self.profiles:
            self.profiles[student_id].last_active = datetime.now()
            self.profiles[student_id].total_sessions += 1
            self.update_streak(student_id)
        
        return session
    
    def end_learning_session(self, session: LearningSession, performance_data: Dict):
        """End a learning session and update metrics"""
        session.end_time = datetime.now()
        session.accuracy = performance_data.get('accuracy', 0.0)
        session.avg_response_time = performance_data.get('avg_response_time', 0.0)
        session.tasks_completed = performance_data.get('completed_tasks', [])
        
        # Calculate focus score based on response time consistency
        response_times = performance_data.get('response_times', [])
        if response_times:
            std_dev = np.std(response_times)
            mean_time = np.mean(response_times)
            # Lower variation = higher focus
            session.focus_score = max(0, min(1, 1 - (std_dev / mean_time) if mean_time > 0 else 0))
        
        # Update student profile
        student_id = session.student_id
        if student_id in self.profiles:
            profile = self.profiles[student_id]
            profile.total_time_spent += session.duration_minutes()
            
            # Update skill levels based on performance
            self.update_skill_levels(student_id, performance_data)
            
            self.save_profile(profile)
        
        # Save session data
        self.save_session(session)
    
    def save_session(self, session: LearningSession):
        """Save session data to disk"""
        filepath = os.path.join(self.data_dir, "sessions", f"{session.session_id}.json")
        data = {
            'session_id': session.session_id,
            'student_id': session.student_id,
            'start_time': session.start_time.isoformat(),
            'end_time': session.end_time.isoformat() if session.end_time else None,
            'tasks_attempted': session.tasks_attempted,
            'tasks_completed': session.tasks_completed,
            'accuracy': session.accuracy,
            'avg_response_time': session.avg_response_time,
            'focus_score': session.focus_score,
            'notes': session.notes
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def update_streak(self, student_id: str):
        """Update learning streak for a student"""
        if student_id not in self.profiles:
            return
        
        profile = self.profiles[student_id]
        sessions = self.sessions.get(student_id, [])
        
        if not sessions:
            return
        
        # Check if there was activity yesterday
        yesterday = datetime.now().date() - timedelta(days=1)
        had_yesterday_activity = any(
            s.start_time.date() == yesterday for s in sessions
        )
        
        if had_yesterday_activity:
            profile.current_streak += 1
            profile.longest_streak = max(profile.longest_streak, profile.current_streak)
        else:
            # Check if there's activity today (not breaking streak)
            today = datetime.now().date()
            had_today_activity = any(
                s.start_time.date() == today for s in sessions
            )
            if not had_today_activity:
                profile.current_streak = 1
    
    def update_skill_levels(self, student_id: str, performance_data: Dict):
        """Update skill levels based on performance"""
        if student_id not in self.profiles:
            return
        
        profile = self.profiles[student_id]
        
        # Map question types to skills
        skill_mapping = {
            'keywords': 'keyword_identification',
            'center_sentence': 'center_sentence',
            'center_paragraph': 'center_paragraph',
            'topic': 'topic_comprehension'
        }
        
        for q_type, skill in skill_mapping.items():
            if q_type in performance_data:
                accuracy = performance_data[q_type].get('accuracy', 0)
                current_level = profile.skill_levels.get(skill, 50)
                
                # Exponential moving average for skill update
                alpha = 0.2  # Learning rate
                new_level = (1 - alpha) * current_level + alpha * (accuracy * 100)
                profile.skill_levels[skill] = min(100, max(0, new_level))
    
    def assess_skill(self, student_id: str, skill_name: str, 
                    performance: float) -> SkillAssessment:
        """Assess a specific skill based on recent performance"""
        if student_id not in self.skill_assessments:
            self.skill_assessments[student_id] = {}
        
        assessments = self.skill_assessments[student_id]
        
        if skill_name in assessments:
            assessment = assessments[skill_name]
            old_level = assessment.current_level
            
            # Update with weighted average
            weight = 0.3  # Weight for new performance
            assessment.current_level = (1 - weight) * old_level + weight * performance
            
            # Determine trend
            if assessment.current_level > old_level + 5:
                assessment.trend = "improving"
            elif assessment.current_level < old_level - 5:
                assessment.trend = "declining"
            else:
                assessment.trend = "stable"
            
            assessment.last_assessed = datetime.now()
            assessment.assessment_count += 1
        else:
            assessment = SkillAssessment(
                skill_name=skill_name,
                current_level=performance,
                trend="stable",
                last_assessed=datetime.now(),
                assessment_count=1,
                recommendations=[]
            )
            assessments[skill_name] = assessment
        
        # Generate recommendations
        assessment.recommendations = self.generate_skill_recommendations(assessment)
        
        return assessment
    
    def generate_skill_recommendations(self, assessment: SkillAssessment) -> List[str]:
        """Generate recommendations for skill improvement"""
        recommendations = []
        
        skill_strategies = {
            'keyword_identification': {
                'low': "핵심 단어 찾기 연습: 문단을 읽고 가장 중요한 3-5개 단어를 선택하세요.",
                'medium': "문맥에서 키워드 관계 파악: 선택한 키워드들이 서로 어떻게 연결되는지 설명하세요.",
                'high': "고급 키워드 분석: 추상적 개념을 나타내는 키워드를 식별하고 설명하세요."
            },
            'center_sentence': {
                'low': "각 문단의 첫 문장과 마지막 문장을 비교하여 주제문을 찾는 연습을 하세요.",
                'medium': "문단 구조 분석: 주제문과 뒷받침 문장을 구분하는 연습을 하세요.",
                'high': "암시적 주제문 파악: 직접 드러나지 않는 중심 생각을 추론하세요."
            },
            'topic_comprehension': {
                'low': "글 전체를 한 문장으로 요약하는 연습을 매일 하세요.",
                'medium': "단락별 요약 후 전체 주제로 통합하는 연습을 하세요.",
                'high': "글쓴이의 의도와 숨겨진 메시지를 파악하는 연습을 하세요."
            }
        }
        
        if assessment.skill_name in skill_strategies:
            strategies = skill_strategies[assessment.skill_name]
            
            if assessment.current_level < 40:
                level = 'low'
            elif assessment.current_level < 70:
                level = 'medium'
            else:
                level = 'high'
            
            recommendations.append(strategies[level])
            
            # Add trend-based recommendations
            if assessment.trend == "declining":
                recommendations.append("기초 개념을 다시 복습하고 쉬운 문제부터 시작하세요.")
            elif assessment.trend == "improving":
                recommendations.append("좋은 진전을 보이고 있습니다! 더 도전적인 문제를 시도해보세요.")
        
        return recommendations
    
    def generate_learning_path(self, student_id: str, 
                              goal_period_days: int = 30) -> Dict[str, Any]:
        """Generate personalized learning path for a student"""
        if student_id not in self.profiles:
            return {}
        
        profile = self.profiles[student_id]
        learning_path = {
            'student_id': student_id,
            'created_at': datetime.now().isoformat(),
            'goal_period_days': goal_period_days,
            'current_level': self._calculate_overall_level(profile),
            'target_level': min(100, self._calculate_overall_level(profile) + 15),
            'weekly_goals': [],
            'recommended_topics': [],
            'practice_schedule': [],
            'milestones': []
        }
        
        # Identify weak areas
        weak_skills = [
            skill for skill, level in profile.skill_levels.items()
            if level < 60
        ]
        
        # Generate weekly goals
        weeks = goal_period_days // 7
        for week in range(1, weeks + 1):
            weekly_goal = {
                'week': week,
                'focus_skill': weak_skills[min(week - 1, len(weak_skills) - 1)] if weak_skills else 'general',
                'target_exercises': 15,
                'target_accuracy': 0.7 + (week * 0.05),
                'recommended_difficulty': self._recommend_difficulty(profile, week)
            }
            learning_path['weekly_goals'].append(weekly_goal)
        
        # Recommend topics based on performance
        learning_path['recommended_topics'] = self._recommend_topics(profile)
        
        # Create practice schedule
        learning_path['practice_schedule'] = self._create_practice_schedule(profile, goal_period_days)
        
        # Set milestones
        learning_path['milestones'] = self._set_milestones(profile, goal_period_days)
        
        # Save learning path
        self.save_learning_path(student_id, learning_path)
        
        return learning_path
    
    def _calculate_overall_level(self, profile: StudentProfile) -> float:
        """Calculate overall skill level"""
        if not profile.skill_levels:
            return 50.0
        return np.mean(list(profile.skill_levels.values()))
    
    def _recommend_difficulty(self, profile: StudentProfile, week: int) -> str:
        """Recommend difficulty level based on current performance"""
        overall_level = self._calculate_overall_level(profile)
        
        if overall_level < 40:
            return "easy"
        elif overall_level < 60:
            return "easy" if week <= 2 else "medium"
        elif overall_level < 80:
            return "medium" if week <= 2 else "hard"
        else:
            return "hard"
    
    def _recommend_topics(self, profile: StudentProfile) -> List[str]:
        """Recommend topics based on student interests and weak areas"""
        # This would be enhanced with actual topic performance data
        topics = [
            "과학 기술",
            "역사 문화",
            "환경 보호",
            "경제 사회",
            "예술 문학"
        ]
        
        # Prioritize based on past performance (placeholder logic)
        weak_skill = min(profile.skill_levels.items(), key=lambda x: x[1])[0]
        
        if 'keyword' in weak_skill:
            topics.insert(0, "어휘가 풍부한 설명문")
        elif 'center' in weak_skill:
            topics.insert(0, "구조가 명확한 논설문")
        elif 'topic' in weak_skill:
            topics.insert(0, "주제가 명확한 설득문")
        
        return topics[:5]
    
    def _create_practice_schedule(self, profile: StudentProfile, 
                                 goal_period_days: int) -> List[Dict]:
        """Create detailed practice schedule"""
        schedule = []
        
        # Determine optimal practice frequency
        if profile.current_streak > 7:
            daily_practice = True
            session_duration = 30
        else:
            daily_practice = False
            session_duration = 45
        
        for day in range(1, goal_period_days + 1):
            if daily_practice or day % 2 == 1:  # Every other day if not daily
                session = {
                    'day': day,
                    'duration_minutes': session_duration,
                    'focus_area': self._get_focus_area_for_day(profile, day),
                    'exercise_count': 5 if session_duration == 30 else 7,
                    'difficulty_mix': {
                        'easy': 0.2,
                        'medium': 0.5,
                        'hard': 0.3
                    }
                }
                schedule.append(session)
        
        return schedule
    
    def _get_focus_area_for_day(self, profile: StudentProfile, day: int) -> str:
        """Determine focus area for a specific day"""
        weak_skills = sorted(profile.skill_levels.items(), key=lambda x: x[1])
        
        # Rotate through weak skills
        skill_index = (day - 1) % min(3, len(weak_skills))
        return weak_skills[skill_index][0]
    
    def _set_milestones(self, profile: StudentProfile, 
                       goal_period_days: int) -> List[Dict]:
        """Set learning milestones"""
        milestones = []
        current_level = self._calculate_overall_level(profile)
        
        milestone_dates = [7, 14, 21, goal_period_days]
        milestone_targets = [
            current_level + 5,
            current_level + 10,
            current_level + 13,
            current_level + 15
        ]
        
        for date, target in zip(milestone_dates, milestone_targets):
            milestones.append({
                'day': date,
                'target_level': min(100, target),
                'reward': self._get_milestone_reward(date),
                'assessment_required': True
            })
        
        return milestones
    
    def _get_milestone_reward(self, day: int) -> str:
        """Get reward for reaching milestone"""
        rewards = {
            7: "일주일 연속 학습 배지",
            14: "꾸준한 학습자 인증",
            21: "3주 마스터 배지",
            30: "월간 목표 달성 인증서"
        }
        return rewards.get(day, f"{day}일 학습 인증")
    
    def save_learning_path(self, student_id: str, learning_path: Dict):
        """Save learning path to disk"""
        filepath = os.path.join(
            self.data_dir, 
            "learning_paths", 
            f"{student_id}_{datetime.now().strftime('%Y%m%d')}.json"
        )
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(learning_path, f, ensure_ascii=False, indent=2)
    
    def track_progress(self, student_id: str) -> Dict[str, Any]:
        """Track student progress against learning path"""
        if student_id not in self.profiles:
            return {}
        
        profile = self.profiles[student_id]
        sessions = self.sessions.get(student_id, [])
        
        # Calculate progress metrics
        progress = {
            'student_id': student_id,
            'overall_progress': self._calculate_overall_level(profile),
            'sessions_completed': len(sessions),
            'total_time_spent': profile.total_time_spent,
            'current_streak': profile.current_streak,
            'skill_improvements': {},
            'achievements_earned': profile.achievements,
            'next_milestone': None,
            'recommendations': []
        }
        
        # Calculate skill improvements
        for skill, level in profile.skill_levels.items():
            initial_level = 50.0  # Default starting level
            improvement = level - initial_level
            progress['skill_improvements'][skill] = {
                'current': level,
                'improvement': improvement,
                'status': 'improving' if improvement > 0 else 'needs_work'
            }
        
        # Find next milestone
        learning_path_files = glob.glob(
            os.path.join(self.data_dir, "learning_paths", f"{student_id}_*.json")
        )
        if learning_path_files:
            # Get most recent learning path
            latest_path_file = max(learning_path_files)
            with open(latest_path_file, 'r', encoding='utf-8') as f:
                learning_path = json.load(f)
                
                for milestone in learning_path.get('milestones', []):
                    if milestone['target_level'] > progress['overall_progress']:
                        progress['next_milestone'] = milestone
                        break
        
        # Generate progress-based recommendations
        if progress['overall_progress'] < 40:
            progress['recommendations'].append("기초 학습에 더 집중하세요.")
        elif progress['overall_progress'] < 70:
            progress['recommendations'].append("중급 난이도 문제에 도전해보세요.")
        else:
            progress['recommendations'].append("고급 문제로 실력을 더욱 향상시키세요.")
        
        if profile.current_streak == 0:
            progress['recommendations'].append("매일 조금씩이라도 학습을 이어가세요.")
        elif profile.current_streak > 7:
            progress['recommendations'].append("훌륭한 학습 습관을 유지하고 있습니다!")
        
        return progress
    
    def get_detailed_report(self, student_id: str) -> Dict[str, Any]:
        """Generate detailed progress report for a student"""
        if student_id not in self.profiles:
            return {}
        
        profile = self.profiles[student_id]
        sessions = self.sessions.get(student_id, [])
        assessments = self.skill_assessments.get(student_id, {})
        
        report = {
            'student_info': {
                'id': student_id,
                'name': profile.name,
                'class_id': profile.class_id,
                'member_since': profile.created_at.isoformat(),
                'last_active': profile.last_active.isoformat()
            },
            'learning_statistics': {
                'total_sessions': profile.total_sessions,
                'total_time_hours': profile.total_time_spent / 60,
                'avg_session_duration': profile.total_time_spent / profile.total_sessions if profile.total_sessions > 0 else 0,
                'current_streak': profile.current_streak,
                'longest_streak': profile.longest_streak
            },
            'skill_analysis': {},
            'recent_sessions': [],
            'achievements': profile.achievements,
            'recommendations': [],
            'predicted_performance': {}
        }
        
        # Skill analysis
        for skill, level in profile.skill_levels.items():
            skill_assessment = assessments.get(skill)
            report['skill_analysis'][skill] = {
                'current_level': level,
                'trend': skill_assessment.trend if skill_assessment else 'unknown',
                'last_assessed': skill_assessment.last_assessed.isoformat() if skill_assessment else None,
                'recommendations': skill_assessment.recommendations if skill_assessment else []
            }
        
        # Recent sessions (last 10)
        recent = sorted(sessions, key=lambda x: x.start_time, reverse=True)[:10]
        for session in recent:
            report['recent_sessions'].append({
                'date': session.start_time.isoformat(),
                'duration_minutes': session.duration_minutes(),
                'accuracy': session.accuracy,
                'focus_score': session.focus_score
            })
        
        # Predict future performance
        if len(sessions) >= 5:
            recent_accuracies = [s.accuracy for s in recent[:5]]
            trend = np.polyfit(range(len(recent_accuracies)), recent_accuracies, 1)[0]
            
            report['predicted_performance'] = {
                'next_session_accuracy': min(1.0, max(0, recent_accuracies[0] + trend)),
                'week_projection': min(1.0, max(0, recent_accuracies[0] + trend * 7)),
                'confidence': 'high' if len(sessions) >= 10 else 'medium'
            }
        
        # Generate personalized recommendations
        weak_skill = min(profile.skill_levels.items(), key=lambda x: x[1])
        report['recommendations'].append(f"{weak_skill[0]} 실력 향상에 집중하세요.")
        
        if profile.current_streak == 0:
            report['recommendations'].append("규칙적인 학습 습관을 만들어보세요.")
        
        if profile.total_time_spent / profile.total_sessions < 20 if profile.total_sessions > 0 else True:
            report['recommendations'].append("세션당 학습 시간을 늘려보세요.")
        
        return report
    
    def export_student_data(self, student_id: str, format: str = 'json') -> str:
        """Export all student data"""
        if student_id not in self.profiles:
            return ""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"student_{student_id}_{timestamp}"
        
        # Gather all data
        export_data = {
            'profile': self.profiles[student_id].to_dict(),
            'sessions': [
                {
                    'session_id': s.session_id,
                    'start_time': s.start_time.isoformat(),
                    'end_time': s.end_time.isoformat() if s.end_time else None,
                    'duration_minutes': s.duration_minutes(),
                    'accuracy': s.accuracy,
                    'focus_score': s.focus_score
                }
                for s in self.sessions.get(student_id, [])
            ],
            'progress': self.track_progress(student_id),
            'detailed_report': self.get_detailed_report(student_id)
        }
        
        if format == 'json':
            filepath = os.path.join(self.data_dir, 'progress_reports', f"{filename}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        elif format == 'csv':
            filepath = os.path.join(self.data_dir, 'progress_reports', f"{filename}.csv")
            # Flatten data for CSV
            df = pd.json_normalize(export_data['profile'])
            df.to_csv(filepath, index=False)
        
        return filepath


def main():
    """Test the student tracker"""
    tracker = StudentTracker()
    
    print("Student Progress Tracker System")
    print("=" * 60)
    
    # Create sample student
    student = tracker.create_student_profile(
        student_id="student_001",
        name="김철수",
        email="kimcs@example.com",
        class_id="class_A"
    )
    
    print(f"Created profile for: {student.name}")
    
    # Start a learning session
    session = tracker.start_learning_session("student_001")
    print(f"Started session: {session.session_id}")
    
    # Simulate performance data
    performance = {
        'accuracy': 0.75,
        'avg_response_time': 45.2,
        'completed_tasks': ['task_1', 'task_2', 'task_3'],
        'response_times': [40, 45, 50, 43, 48],
        'keywords': {'accuracy': 0.8},
        'center_sentence': {'accuracy': 0.7},
        'topic': {'accuracy': 0.75}
    }
    
    # End session
    tracker.end_learning_session(session, performance)
    print("Session ended and data saved")
    
    # Generate learning path
    learning_path = tracker.generate_learning_path("student_001")
    print(f"\nLearning Path Generated:")
    print(f"  Current Level: {learning_path['current_level']:.1f}")
    print(f"  Target Level: {learning_path['target_level']:.1f}")
    print(f"  Weekly Goals: {len(learning_path['weekly_goals'])}")
    
    # Track progress
    progress = tracker.track_progress("student_001")
    print(f"\nProgress Report:")
    print(f"  Overall Progress: {progress['overall_progress']:.1f}")
    print(f"  Sessions Completed: {progress['sessions_completed']}")
    print(f"  Current Streak: {progress['current_streak']} days")
    
    # Get detailed report
    report = tracker.get_detailed_report("student_001")
    print(f"\nDetailed Report Generated")
    print(f"  Skills Analyzed: {len(report['skill_analysis'])}")
    print(f"  Recommendations: {len(report['recommendations'])}")
    
    # Export data
    export_path = tracker.export_student_data("student_001")
    print(f"\nData exported to: {export_path}")


if __name__ == "__main__":
    main()