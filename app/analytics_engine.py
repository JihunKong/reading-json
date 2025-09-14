#!/usr/bin/env python3
"""
Advanced Analytics Engine for Teacher Dashboard
- Deep learning pattern analysis
- Performance prediction
- Intervention recommendations
- Educational insights
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import sqlite3
from collections import defaultdict, Counter
import statistics
from enum import Enum

from app.teacher_data_manager import data_manager, StudentSession, StudentStatus

class AnalysisType(Enum):
    PERFORMANCE_TREND = "performance_trend"
    DIFFICULTY_PATTERN = "difficulty_pattern"
    LEARNING_VELOCITY = "learning_velocity"
    MASTERY_PREDICTION = "mastery_prediction"
    INTERVENTION_NEED = "intervention_need"

@dataclass
class LearningInsight:
    """Individual learning insight"""
    insight_type: str
    confidence: float  # 0-1
    title: str
    description: str
    recommendations: List[str]
    data_points: Dict[str, Any]
    severity: str = "info"  # info, warning, critical

@dataclass
class ClassAnalytics:
    """Comprehensive class analytics"""
    class_id: str
    analysis_timestamp: datetime
    
    # Performance metrics
    overall_performance: float  # 0-1
    performance_trend: str      # improving, declining, stable
    phase_completion_rates: Dict[int, float]
    average_learning_velocity: float
    
    # Student categorization
    high_performers: List[str]
    struggling_students: List[str]
    at_risk_students: List[str]
    
    # Predictions
    expected_completion_time: Dict[str, int]  # student_id -> minutes
    mastery_predictions: Dict[str, float]     # student_id -> predicted mastery
    
    # Insights
    key_insights: List[LearningInsight]
    intervention_recommendations: List[Dict[str, Any]]

class AdvancedAnalyticsEngine:
    """
    Advanced analytics engine for educational insights
    - Pattern recognition in learning behavior
    - Performance prediction
    - Adaptive intervention recommendations
    """
    
    def __init__(self):
        self.learning_patterns = {}
        self.performance_models = {}
        
        # Initialize analysis thresholds
        self.thresholds = {
            'struggling_score': 0.5,
            'at_risk_consecutive_wrong': 3,
            'slow_learner_time_ratio': 2.0,  # 2x average time
            'fast_learner_time_ratio': 0.5,  # 0.5x average time
            'mastery_threshold': 0.75,
            'intervention_threshold': 0.3
        }
        
        print("✅ Advanced Analytics Engine initialized")
    
    def analyze_class(self, class_id: str) -> ClassAnalytics:
        """Perform comprehensive class analysis"""
        # Get all students in class
        class_students = [
            session for session in data_manager.sessions.values() 
            if session.class_id == class_id
        ]
        
        if not class_students:
            return ClassAnalytics(
                class_id=class_id,
                analysis_timestamp=datetime.now(),
                overall_performance=0.0,
                performance_trend="stable",
                phase_completion_rates={},
                average_learning_velocity=0.0,
                high_performers=[],
                struggling_students=[],
                at_risk_students=[],
                expected_completion_time={},
                mastery_predictions={},
                key_insights=[],
                intervention_recommendations=[]
            )
        
        # Perform various analyses
        performance_analysis = self._analyze_performance(class_students)
        learning_velocity_analysis = self._analyze_learning_velocity(class_students)
        student_categorization = self._categorize_students(class_students)
        predictions = self._generate_predictions(class_students)
        insights = self._generate_insights(class_students)
        interventions = self._recommend_interventions(class_students)
        
        return ClassAnalytics(
            class_id=class_id,
            analysis_timestamp=datetime.now(),
            **performance_analysis,
            **learning_velocity_analysis,
            **student_categorization,
            **predictions,
            key_insights=insights,
            intervention_recommendations=interventions
        )
    
    def _analyze_performance(self, students: List[StudentSession]) -> Dict[str, Any]:
        """Analyze overall class performance"""
        if not students:
            return {
                "overall_performance": 0.0,
                "performance_trend": "stable",
                "phase_completion_rates": {}
            }
        
        # Calculate overall performance
        mastery_scores = [s.mastery_level for s in students if s.mastery_level > 0]
        overall_performance = statistics.mean(mastery_scores) if mastery_scores else 0.0
        
        # Calculate phase completion rates
        phase_completion_rates = {}
        for phase in range(1, 5):
            completed = len([s for s in students if phase in s.phase_scores])
            total = len(students)
            phase_completion_rates[phase] = completed / total if total > 0 else 0
        
        # Determine trend (simplified - would use historical data in production)
        trend = "stable"
        if overall_performance > 0.8:
            trend = "improving"
        elif overall_performance < 0.5:
            trend = "declining"
        
        return {
            "overall_performance": overall_performance,
            "performance_trend": trend,
            "phase_completion_rates": phase_completion_rates
        }
    
    def _analyze_learning_velocity(self, students: List[StudentSession]) -> Dict[str, Any]:
        """Analyze learning velocity patterns"""
        velocities = []
        
        for student in students:
            if student.total_time > 0 and len(student.phase_scores) > 0:
                # Questions completed per minute
                velocity = len(student.phase_scores) * 60 / student.total_time
                velocities.append(velocity)
        
        avg_velocity = statistics.mean(velocities) if velocities else 0.0
        
        return {"average_learning_velocity": avg_velocity}
    
    def _categorize_students(self, students: List[StudentSession]) -> Dict[str, List[str]]:
        """Categorize students by performance patterns"""
        high_performers = []
        struggling_students = []
        at_risk_students = []
        
        for student in students:
            # High performers: high mastery and consistent performance
            if (student.mastery_level >= 0.8 and 
                student.consecutive_wrong <= 1 and 
                not student.help_requested):
                high_performers.append(student.student_id)
            
            # Struggling students: currently having difficulties
            elif (student.status == StudentStatus.STRUGGLING or
                  student.consecutive_wrong >= 2 or
                  student.help_requested):
                struggling_students.append(student.student_id)
            
            # At risk: showing warning signs
            elif (student.mastery_level < 0.6 or
                  student.consecutive_wrong >= self.thresholds['at_risk_consecutive_wrong'] or
                  len(student.difficulty_indicators) > 2):
                at_risk_students.append(student.student_id)
        
        return {
            "high_performers": high_performers,
            "struggling_students": struggling_students,
            "at_risk_students": at_risk_students
        }
    
    def _generate_predictions(self, students: List[StudentSession]) -> Dict[str, Dict[str, Any]]:
        """Generate predictions for student performance"""
        expected_completion_time = {}
        mastery_predictions = {}
        
        for student in students:
            # Predict completion time based on current velocity
            if student.total_time > 0 and len(student.phase_scores) > 0:
                avg_time_per_phase = student.total_time / len(student.phase_scores)
                remaining_phases = 4 - len(student.phase_scores)
                expected_completion_time[student.student_id] = int(
                    avg_time_per_phase * remaining_phases / 60  # Convert to minutes
                )
            
            # Predict final mastery based on current trajectory
            if len(student.accuracy_trend) >= 3:
                # Simple linear trend prediction
                recent_scores = student.accuracy_trend[-3:]
                if len(recent_scores) >= 2:
                    trend = (recent_scores[-1] - recent_scores[0]) / (len(recent_scores) - 1)
                    predicted_mastery = min(1.0, max(0.0, student.mastery_level + trend))
                    mastery_predictions[student.student_id] = predicted_mastery
        
        return {
            "expected_completion_time": expected_completion_time,
            "mastery_predictions": mastery_predictions
        }
    
    def _generate_insights(self, students: List[StudentSession]) -> List[LearningInsight]:
        """Generate educational insights from data"""
        insights = []
        
        # Insight 1: Phase difficulty analysis
        phase_difficulties = self._analyze_phase_difficulties(students)
        if phase_difficulties:
            insights.append(LearningInsight(
                insight_type="phase_difficulty",
                confidence=0.8,
                title="단계별 난이도 분석",
                description=f"학생들이 {phase_difficulties['hardest_phase']}단계에서 가장 어려워하고 있습니다.",
                recommendations=[
                    f"{phase_difficulties['hardest_phase']}단계 설명을 강화하세요",
                    "추가 연습 문제를 제공하세요",
                    "개별 지도 시간을 늘려보세요"
                ],
                data_points=phase_difficulties,
                severity="warning" if phase_difficulties['difficulty_score'] > 0.7 else "info"
            ))
        
        # Insight 2: Learning velocity patterns
        velocity_insight = self._analyze_velocity_patterns(students)
        if velocity_insight:
            insights.append(velocity_insight)
        
        # Insight 3: Help request patterns
        help_pattern_insight = self._analyze_help_patterns(students)
        if help_pattern_insight:
            insights.append(help_pattern_insight)
        
        # Insight 4: Time-of-day performance patterns (if available)
        # This would require session timing data
        
        return insights
    
    def _analyze_phase_difficulties(self, students: List[StudentSession]) -> Optional[Dict[str, Any]]:
        """Analyze which phases are most difficult"""
        phase_scores = defaultdict(list)
        phase_attempts = defaultdict(list)
        
        for student in students:
            for phase, score in student.phase_scores.items():
                phase_scores[phase].append(score)
                attempts = student.phase_attempts.get(phase, 1)
                phase_attempts[phase].append(attempts)
        
        if not phase_scores:
            return None
        
        # Calculate difficulty metrics for each phase
        phase_difficulties = {}
        for phase in range(1, 5):
            if phase in phase_scores:
                avg_score = statistics.mean(phase_scores[phase])
                avg_attempts = statistics.mean(phase_attempts[phase])
                
                # Difficulty score: lower scores and higher attempts = more difficult
                difficulty = (1 - avg_score) * 0.7 + (avg_attempts - 1) * 0.3
                phase_difficulties[phase] = {
                    "avg_score": avg_score,
                    "avg_attempts": avg_attempts,
                    "difficulty": difficulty
                }
        
        if not phase_difficulties:
            return None
        
        # Find hardest phase
        hardest_phase = max(phase_difficulties.keys(), 
                          key=lambda p: phase_difficulties[p]["difficulty"])
        
        return {
            "hardest_phase": hardest_phase,
            "difficulty_score": phase_difficulties[hardest_phase]["difficulty"],
            "phase_data": phase_difficulties
        }
    
    def _analyze_velocity_patterns(self, students: List[StudentSession]) -> Optional[LearningInsight]:
        """Analyze learning velocity patterns"""
        velocities = []
        time_data = []
        
        for student in students:
            if student.total_time > 0 and len(student.phase_scores) > 0:
                velocity = len(student.phase_scores) * 60 / student.total_time  # questions/minute
                velocities.append(velocity)
                time_data.append({
                    "student_id": student.student_id,
                    "velocity": velocity,
                    "total_time": student.total_time
                })
        
        if len(velocities) < 3:  # Need minimum data points
            return None
        
        avg_velocity = statistics.mean(velocities)
        velocity_std = statistics.stdev(velocities) if len(velocities) > 1 else 0
        
        # Identify outliers
        fast_learners = [d for d in time_data if d["velocity"] > avg_velocity + velocity_std]
        slow_learners = [d for d in time_data if d["velocity"] < avg_velocity - velocity_std]
        
        description = f"평균 학습 속도: {avg_velocity:.2f}문제/분"
        recommendations = []
        severity = "info"
        
        if len(slow_learners) > len(students) * 0.3:  # More than 30% are slow
            description += f", {len(slow_learners)}명의 학생이 평균보다 느립니다"
            recommendations.extend([
                "느린 학습자를 위한 추가 시간을 고려하세요",
                "개별 맞춤 지도를 제공하세요",
                "학습 자료를 단순화해보세요"
            ])
            severity = "warning"
        
        if len(fast_learners) > len(students) * 0.2:  # More than 20% are fast
            description += f", {len(fast_learners)}명의 학생이 빠르게 완료하고 있습니다"
            recommendations.extend([
                "빠른 학습자를 위한 심화 문제를 준비하세요",
                "멘토 역할을 부여해보세요"
            ])
        
        return LearningInsight(
            insight_type="learning_velocity",
            confidence=0.75,
            title="학습 속도 패턴 분석",
            description=description,
            recommendations=recommendations,
            data_points={
                "average_velocity": avg_velocity,
                "fast_learners": len(fast_learners),
                "slow_learners": len(slow_learners),
                "total_students": len(students)
            },
            severity=severity
        )
    
    def _analyze_help_patterns(self, students: List[StudentSession]) -> Optional[LearningInsight]:
        """Analyze help request and hint usage patterns"""
        help_requests = len([s for s in students if s.help_requested])
        total_students = len(students)
        
        if total_students == 0:
            return None
        
        help_rate = help_requests / total_students
        
        # Analyze hint usage by phase
        phase_hint_usage = defaultdict(int)
        for student in students:
            for phase, hints in student.hints_used.items():
                phase_hint_usage[phase] += hints
        
        # Find phase with most hint usage
        if phase_hint_usage:
            max_hint_phase = max(phase_hint_usage.keys(), key=lambda p: phase_hint_usage[p])
            max_hints = phase_hint_usage[max_hint_phase]
        else:
            max_hint_phase = None
            max_hints = 0
        
        severity = "info"
        if help_rate > 0.4:  # More than 40% need help
            severity = "warning"
        elif help_rate > 0.6:  # More than 60% need help
            severity = "critical"
        
        description = f"전체 학생 중 {help_requests}명({help_rate*100:.0f}%)이 도움을 요청했습니다"
        if max_hint_phase:
            description += f". {max_hint_phase}단계에서 힌트 사용이 가장 많습니다"
        
        recommendations = []
        if help_rate > 0.3:
            recommendations.extend([
                "해당 개념에 대한 추가 설명이 필요합니다",
                "문제 난이도를 재검토하세요",
                "개별 지도 시간을 늘려보세요"
            ])
        
        if max_hints > total_students:  # Average more than 1 hint per student
            recommendations.append(f"{max_hint_phase}단계 설명을 강화하세요")
        
        return LearningInsight(
            insight_type="help_patterns",
            confidence=0.85,
            title="도움 요청 패턴",
            description=description,
            recommendations=recommendations,
            data_points={
                "help_rate": help_rate,
                "help_requests": help_requests,
                "total_students": total_students,
                "max_hint_phase": max_hint_phase,
                "max_hints": max_hints,
                "phase_hint_usage": dict(phase_hint_usage)
            },
            severity=severity
        )
    
    def _recommend_interventions(self, students: List[StudentSession]) -> List[Dict[str, Any]]:
        """Generate specific intervention recommendations"""
        interventions = []
        
        # Identify students needing immediate intervention
        critical_students = [
            s for s in students 
            if (s.consecutive_wrong >= 3 or 
                s.mastery_level < 0.3 or
                len(s.difficulty_indicators) > 3)
        ]
        
        if critical_students:
            interventions.append({
                "type": "immediate_intervention",
                "priority": "high",
                "title": "즉시 개입 필요 학생",
                "description": f"{len(critical_students)}명의 학생이 즉시 도움이 필요합니다",
                "student_ids": [s.student_id for s in critical_students],
                "actions": [
                    "개별 지도 시간 배정",
                    "기초 개념 복습 제공",
                    "학습 속도 조정 고려"
                ]
            })
        
        # Group intervention for common difficulties
        phase_difficulties = defaultdict(list)
        for student in students:
            current_phase = student.current_phase
            if (student.phase_attempts.get(current_phase, 0) > 2 and
                student.phase_scores.get(current_phase, 1.0) < 0.6):
                phase_difficulties[current_phase].append(student.student_id)
        
        for phase, student_ids in phase_difficulties.items():
            if len(student_ids) > 2:  # Multiple students struggling with same phase
                interventions.append({
                    "type": "group_intervention", 
                    "priority": "medium",
                    "title": f"{phase}단계 그룹 지도",
                    "description": f"{len(student_ids)}명이 {phase}단계에서 어려워하고 있습니다",
                    "student_ids": student_ids,
                    "actions": [
                        f"{phase}단계 개념 재설명",
                        "추가 연습 문제 제공",
                        "동료 학습 그룹 구성"
                    ]
                })
        
        # Enrichment for high performers
        high_performers = [
            s for s in students 
            if s.mastery_level >= 0.9 and s.status == StudentStatus.COMPLETED
        ]
        
        if len(high_performers) >= 2:
            interventions.append({
                "type": "enrichment",
                "priority": "low",
                "title": "우수 학습자 심화 학습",
                "description": f"{len(high_performers)}명의 우수 학습자가 심화 학습이 가능합니다",
                "student_ids": [s.student_id for s in high_performers],
                "actions": [
                    "심화 문제 제공",
                    "멘토 역할 부여",
                    "창의적 과제 도전"
                ]
            })
        
        return interventions
    
    def generate_performance_report(self, class_id: str) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        analytics = self.analyze_class(class_id)
        
        # Create detailed report
        report = {
            "class_id": class_id,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_students": len(data_manager.sessions),
                "overall_performance": analytics.overall_performance,
                "performance_trend": analytics.performance_trend,
                "completion_rate": analytics.phase_completion_rates.get(4, 0),
                "intervention_needed": len(analytics.struggling_students) + len(analytics.at_risk_students)
            },
            "detailed_metrics": {
                "phase_completion_rates": analytics.phase_completion_rates,
                "learning_velocity": analytics.average_learning_velocity,
                "student_categorization": {
                    "high_performers": len(analytics.high_performers),
                    "struggling": len(analytics.struggling_students),
                    "at_risk": len(analytics.at_risk_students)
                }
            },
            "insights": [
                {
                    "type": insight.insight_type,
                    "confidence": insight.confidence,
                    "title": insight.title,
                    "description": insight.description,
                    "recommendations": insight.recommendations,
                    "severity": insight.severity
                }
                for insight in analytics.key_insights
            ],
            "interventions": analytics.intervention_recommendations,
            "predictions": {
                "expected_completion_times": analytics.expected_completion_time,
                "mastery_predictions": analytics.mastery_predictions
            }
        }
        
        return report
    
    def get_student_learning_profile(self, student_id: str) -> Dict[str, Any]:
        """Generate detailed learning profile for individual student"""
        if student_id not in data_manager.sessions:
            return None
        
        student = data_manager.sessions[student_id]
        
        # Learning behavior analysis
        learning_style = self._analyze_learning_style(student)
        strength_areas = self._identify_strengths(student)
        improvement_areas = self._identify_improvement_areas(student)
        
        profile = {
            "student_id": student_id,
            "student_name": student.student_name,
            "generated_at": datetime.now().isoformat(),
            
            "current_status": {
                "phase": student.current_phase,
                "status": student.status.value,
                "mastery_level": student.mastery_level,
                "total_time": student.total_time
            },
            
            "learning_behavior": {
                "learning_style": learning_style,
                "help_seeking_frequency": len(student.difficulty_indicators),
                "hint_dependency": sum(student.hints_used.values()),
                "persistence_level": self._calculate_persistence(student)
            },
            
            "performance_analysis": {
                "strength_areas": strength_areas,
                "improvement_areas": improvement_areas,
                "phase_performance": student.phase_scores,
                "accuracy_trend": student.accuracy_trend
            },
            
            "recommendations": {
                "immediate_actions": self._generate_student_recommendations(student),
                "learning_strategies": self._suggest_learning_strategies(student),
                "motivational_approaches": self._suggest_motivational_approaches(student)
            }
        }
        
        return profile
    
    def _analyze_learning_style(self, student: StudentSession) -> str:
        """Analyze student's learning style based on behavior"""
        hint_usage = sum(student.hints_used.values())
        help_requests = 1 if student.help_requested else 0
        avg_time_per_phase = student.total_time / max(len(student.phase_scores), 1)
        
        if hint_usage > 5:
            return "guidance_dependent"  # Needs frequent hints
        elif help_requests > 0:
            return "collaborative"  # Seeks teacher help
        elif avg_time_per_phase < 60:
            return "quick_processor"  # Fast learner
        elif avg_time_per_phase > 180:
            return "deliberate_processor"  # Careful, methodical
        else:
            return "independent"  # Self-directed
    
    def _identify_strengths(self, student: StudentSession) -> List[str]:
        """Identify student's strength areas"""
        strengths = []
        
        # Check phase performance
        for phase, score in student.phase_scores.items():
            if score >= 0.8:
                phase_names = {
                    1: "성분 식별",
                    2: "필요성 판단", 
                    3: "일반화",
                    4: "주제 재구성"
                }
                strengths.append(phase_names.get(phase, f"{phase}단계"))
        
        # Check learning behaviors
        if student.consecutive_wrong <= 1:
            strengths.append("일관된 정확성")
        
        if student.total_time > 0 and len(student.phase_scores) > 2:
            avg_time = student.total_time / len(student.phase_scores)
            if avg_time < 90:  # Less than 1.5 minutes per phase
                strengths.append("빠른 학습")
        
        if sum(student.hints_used.values()) <= 2:
            strengths.append("독립적 학습")
        
        return strengths if strengths else ["추가 데이터 필요"]
    
    def _identify_improvement_areas(self, student: StudentSession) -> List[str]:
        """Identify areas for improvement"""
        improvements = []
        
        # Check phase performance
        for phase, score in student.phase_scores.items():
            if score < 0.6:
                phase_names = {
                    1: "성분 식별 능력",
                    2: "필요성 판단 능력",
                    3: "일반화 능력", 
                    4: "주제 재구성 능력"
                }
                improvements.append(phase_names.get(phase, f"{phase}단계 숙련도"))
        
        # Check learning behaviors
        if student.consecutive_wrong >= 2:
            improvements.append("정확성 향상")
        
        if sum(student.hints_used.values()) > 5:
            improvements.append("독립적 문제해결")
        
        if len(student.difficulty_indicators) > 3:
            improvements.append("학습 전략 개선")
        
        return improvements if improvements else ["전반적으로 양호함"]
    
    def _calculate_persistence(self, student: StudentSession) -> str:
        """Calculate student's persistence level"""
        total_attempts = sum(student.phase_attempts.values())
        phases_attempted = len(student.phase_attempts)
        
        if phases_attempted == 0:
            return "insufficient_data"
        
        avg_attempts = total_attempts / phases_attempted
        
        if avg_attempts > 3:
            return "high"  # Keeps trying despite difficulties
        elif avg_attempts > 1.5:
            return "medium"
        else:
            return "low"  # Gives up quickly
    
    def _generate_student_recommendations(self, student: StudentSession) -> List[str]:
        """Generate specific recommendations for student"""
        recommendations = []
        
        if student.consecutive_wrong >= 2:
            recommendations.append("기본 개념 복습 제공")
        
        if sum(student.hints_used.values()) > 3:
            recommendations.append("독립적 문제해결 연습")
        
        if student.mastery_level < 0.5:
            recommendations.append("개별 지도 시간 증가")
        
        if student.mastery_level >= 0.9:
            recommendations.append("심화 학습 기회 제공")
        
        return recommendations if recommendations else ["현재 학습 방향 유지"]
    
    def _suggest_learning_strategies(self, student: StudentSession) -> List[str]:
        """Suggest learning strategies based on student profile"""
        learning_style = self._analyze_learning_style(student)
        
        strategies = {
            "guidance_dependent": [
                "단계별 체크리스트 제공",
                "예시 문제 먼저 풀어보기",
                "점진적 힌트 시스템 활용"
            ],
            "collaborative": [
                "그룹 토론 활동 참여",
                "동료 학습 파트너 배정",
                "교사와의 정기 점검 면담"
            ],
            "quick_processor": [
                "심화 문제 도전",
                "복합적 사고 문제 제공",
                "창의적 접근법 시도"
            ],
            "deliberate_processor": [
                "충분한 사고 시간 제공",
                "단계별 점검 확인",
                "개념 정리 시간 확보"
            ],
            "independent": [
                "자기주도학습 환경 조성",
                "다양한 문제 유형 탐색",
                "메타인지 전략 활용"
            ]
        }
        
        return strategies.get(learning_style, ["개별 맞춤 전략 필요"])
    
    def _suggest_motivational_approaches(self, student: StudentSession) -> List[str]:
        """Suggest motivational approaches for student"""
        approaches = []
        
        if student.mastery_level >= 0.8:
            approaches.extend([
                "성취감 강화 피드백",
                "리더십 역할 부여",
                "도전적 목표 설정"
            ])
        elif student.mastery_level >= 0.6:
            approaches.extend([
                "점진적 목표 설정",
                "성공 경험 강조",
                "동료 비교보다는 개인 성장 강조"
            ])
        else:
            approaches.extend([
                "작은 성공 경험 제공",
                "격려와 지지 강화",
                "흥미 유발 활동 추가"
            ])
        
        return approaches

# Global analytics engine instance
analytics_engine = AdvancedAnalyticsEngine()