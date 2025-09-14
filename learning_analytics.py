#!/usr/bin/env python3
"""
Korean Reading Comprehension Learning Analytics System
Main analytics engine for comprehensive educational data analysis
"""

import json
import os
import glob
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict, Counter
import statistics
import numpy as np
from dataclasses import dataclass, asdict
import pandas as pd


@dataclass
class PerformanceMetrics:
    """Student performance metrics data structure"""
    student_id: str
    total_attempts: int
    correct_answers: int
    accuracy: float
    avg_similarity_score: float
    avg_response_time: float
    keyword_accuracy: float
    center_sentence_accuracy: float
    topic_accuracy: float
    strengths: List[str]
    weaknesses: List[str]
    improvement_trend: float
    last_activity: datetime
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['last_activity'] = self.last_activity.isoformat()
        return data


@dataclass
class ClassMetrics:
    """Class-level performance metrics"""
    class_id: str
    total_students: int
    active_students: int
    avg_accuracy: float
    median_accuracy: float
    std_deviation: float
    top_performers: List[str]
    struggling_students: List[str]
    common_mistakes: List[Dict[str, Any]]
    topic_performance: Dict[str, float]
    question_type_performance: Dict[str, float]
    completion_rate: float
    engagement_score: float
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class LearningAnalyticsEngine:
    """Main analytics engine for Korean reading comprehension education"""
    
    def __init__(self, data_dir: str = "./analytics_data"):
        """
        Initialize the analytics engine
        
        Args:
            data_dir: Directory for storing analytics data
        """
        self.data_dir = data_dir
        self.ensure_directories()
        self.performance_cache = {}
        self.class_cache = {}
        self.learning_patterns = defaultdict(list)
        
    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        dirs = [
            self.data_dir,
            os.path.join(self.data_dir, "student_data"),
            os.path.join(self.data_dir, "class_data"),
            os.path.join(self.data_dir, "reports"),
            os.path.join(self.data_dir, "visualizations"),
            os.path.join(self.data_dir, "exports")
        ]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    def load_submission_data(self, submission_file: str) -> pd.DataFrame:
        """
        Load student submission data from CSV
        
        Args:
            submission_file: Path to submission CSV file
            
        Returns:
            DataFrame with submission data
        """
        try:
            df = pd.read_csv(submission_file)
            # Add timestamp if not present
            if 'timestamp' not in df.columns:
                df['timestamp'] = datetime.now().isoformat()
            return df
        except Exception as e:
            print(f"Error loading submission data: {e}")
            return pd.DataFrame()
    
    def load_task_items(self, items_dir: str) -> Dict[str, Dict]:
        """
        Load task items from JSON files
        
        Args:
            items_dir: Directory containing task JSON files
            
        Returns:
            Dictionary mapping task IDs to task data
        """
        items = {}
        json_files = glob.glob(os.path.join(items_dir, "*.json"))
        
        for filepath in json_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    items[data['id']] = data
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
                
        return items
    
    def analyze_student_performance(self, 
                                   student_id: str,
                                   submissions: pd.DataFrame,
                                   tasks: Dict[str, Dict]) -> PerformanceMetrics:
        """
        Analyze individual student performance
        
        Args:
            student_id: Student identifier
            submissions: DataFrame of student submissions
            tasks: Dictionary of task items
            
        Returns:
            PerformanceMetrics object with detailed analysis
        """
        student_subs = submissions[submissions['user_id'] == student_id]
        
        if student_subs.empty:
            return None
        
        # Calculate basic metrics
        total_attempts = len(student_subs)
        correct_answers = len(student_subs[student_subs['is_correct'] == True])
        accuracy = correct_answers / total_attempts if total_attempts > 0 else 0
        
        # Calculate similarity scores for free-response questions
        similarity_scores = student_subs['similarity'].dropna()
        avg_similarity = similarity_scores.mean() if not similarity_scores.empty else 0
        
        # Calculate response times
        if 'response_time' in student_subs.columns:
            response_times = student_subs['response_time'].dropna()
            avg_response_time = response_times.mean() if not response_times.empty else 0
        else:
            avg_response_time = 0
        
        # Analyze by question type
        keyword_subs = student_subs[student_subs['question_type'] == 'keywords']
        center_subs = student_subs[student_subs['question_type'].str.contains('center', na=False)]
        topic_subs = student_subs[student_subs['question_type'] == 'topic']
        
        keyword_accuracy = self._calculate_accuracy(keyword_subs)
        center_accuracy = self._calculate_accuracy(center_subs)
        topic_accuracy = self._calculate_accuracy(topic_subs)
        
        # Identify strengths and weaknesses
        strengths = []
        weaknesses = []
        
        if keyword_accuracy > 0.8:
            strengths.append("키워드 식별")
        elif keyword_accuracy < 0.5:
            weaknesses.append("키워드 식별")
            
        if center_accuracy > 0.7:
            strengths.append("중심 문장/단락 파악")
        elif center_accuracy < 0.5:
            weaknesses.append("중심 문장/단락 파악")
            
        if topic_accuracy > 0.75:
            strengths.append("주제 파악")
        elif topic_accuracy < 0.5:
            weaknesses.append("주제 파악")
        
        # Calculate improvement trend
        improvement_trend = self._calculate_improvement_trend(student_subs)
        
        # Get last activity
        if 'timestamp' in student_subs.columns:
            last_activity = pd.to_datetime(student_subs['timestamp']).max()
        else:
            last_activity = datetime.now()
        
        return PerformanceMetrics(
            student_id=student_id,
            total_attempts=total_attempts,
            correct_answers=correct_answers,
            accuracy=accuracy,
            avg_similarity_score=avg_similarity,
            avg_response_time=avg_response_time,
            keyword_accuracy=keyword_accuracy,
            center_sentence_accuracy=center_accuracy,
            topic_accuracy=topic_accuracy,
            strengths=strengths,
            weaknesses=weaknesses,
            improvement_trend=improvement_trend,
            last_activity=last_activity
        )
    
    def _calculate_accuracy(self, submissions: pd.DataFrame) -> float:
        """Calculate accuracy for a subset of submissions"""
        if submissions.empty:
            return 0.0
        correct = len(submissions[submissions['is_correct'] == True])
        total = len(submissions)
        return correct / total if total > 0 else 0.0
    
    def _calculate_improvement_trend(self, submissions: pd.DataFrame) -> float:
        """
        Calculate improvement trend over time
        
        Returns:
            Float between -1 and 1 indicating trend direction
        """
        if len(submissions) < 3:
            return 0.0
        
        # Sort by timestamp
        sorted_subs = submissions.sort_values('timestamp') if 'timestamp' in submissions.columns else submissions
        
        # Calculate rolling accuracy
        window_size = min(5, len(sorted_subs) // 2)
        if window_size < 2:
            return 0.0
        
        rolling_correct = sorted_subs['is_correct'].rolling(window=window_size, min_periods=1).mean()
        
        # Calculate trend using linear regression
        x = np.arange(len(rolling_correct))
        y = rolling_correct.fillna(0).values
        
        if len(x) > 1:
            slope = np.polyfit(x, y, 1)[0]
            return np.clip(slope * 10, -1, 1)  # Normalize to [-1, 1]
        
        return 0.0
    
    def analyze_class_performance(self,
                                 class_id: str,
                                 submissions: pd.DataFrame,
                                 tasks: Dict[str, Dict]) -> ClassMetrics:
        """
        Analyze class-level performance
        
        Args:
            class_id: Class identifier
            submissions: DataFrame of all submissions
            tasks: Dictionary of task items
            
        Returns:
            ClassMetrics object with class analysis
        """
        # Get unique students
        students = submissions['user_id'].unique()
        total_students = len(students)
        
        # Calculate active students (submitted in last 7 days)
        if 'timestamp' in submissions.columns:
            recent_date = datetime.now() - timedelta(days=7)
            recent_subs = submissions[pd.to_datetime(submissions['timestamp']) > recent_date]
            active_students = len(recent_subs['user_id'].unique())
        else:
            active_students = total_students
        
        # Calculate accuracy metrics
        student_accuracies = []
        for student_id in students:
            student_subs = submissions[submissions['user_id'] == student_id]
            if not student_subs.empty:
                accuracy = len(student_subs[student_subs['is_correct'] == True]) / len(student_subs)
                student_accuracies.append(accuracy)
        
        avg_accuracy = np.mean(student_accuracies) if student_accuracies else 0
        median_accuracy = np.median(student_accuracies) if student_accuracies else 0
        std_deviation = np.std(student_accuracies) if student_accuracies else 0
        
        # Identify top performers and struggling students
        student_performance = [(s, a) for s, a in zip(students, student_accuracies)]
        student_performance.sort(key=lambda x: x[1], reverse=True)
        
        top_count = min(5, len(student_performance) // 4)
        top_performers = [s[0] for s in student_performance[:top_count]]
        struggling_students = [s[0] for s in student_performance if s[1] < 0.5]
        
        # Analyze common mistakes
        common_mistakes = self._analyze_common_mistakes(submissions, tasks)
        
        # Analyze performance by topic
        topic_performance = self._analyze_topic_performance(submissions, tasks)
        
        # Analyze performance by question type
        question_type_performance = self._analyze_question_type_performance(submissions)
        
        # Calculate completion rate
        expected_tasks = len(tasks) if tasks else 1
        completion_rate = len(submissions) / (total_students * expected_tasks) if total_students > 0 else 0
        completion_rate = min(1.0, completion_rate)  # Cap at 100%
        
        # Calculate engagement score
        engagement_score = self._calculate_engagement_score(submissions, active_students, total_students)
        
        return ClassMetrics(
            class_id=class_id,
            total_students=total_students,
            active_students=active_students,
            avg_accuracy=avg_accuracy,
            median_accuracy=median_accuracy,
            std_deviation=std_deviation,
            top_performers=top_performers,
            struggling_students=struggling_students,
            common_mistakes=common_mistakes,
            topic_performance=topic_performance,
            question_type_performance=question_type_performance,
            completion_rate=completion_rate,
            engagement_score=engagement_score
        )
    
    def _analyze_common_mistakes(self, 
                                submissions: pd.DataFrame,
                                tasks: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """Analyze and identify common mistakes"""
        mistakes = []
        incorrect_subs = submissions[submissions['is_correct'] == False]
        
        if incorrect_subs.empty:
            return mistakes
        
        # Group by task and question type
        mistake_counts = incorrect_subs.groupby(['task_id', 'question_type']).size()
        
        for (task_id, q_type), count in mistake_counts.items():
            if count >= 3:  # Threshold for "common" mistake
                task = tasks.get(task_id, {})
                mistakes.append({
                    'task_id': task_id,
                    'question_type': q_type,
                    'error_count': int(count),
                    'topic': task.get('topic', 'Unknown'),
                    'difficulty': task.get('difficulty', 'Unknown')
                })
        
        # Sort by error count
        mistakes.sort(key=lambda x: x['error_count'], reverse=True)
        return mistakes[:10]  # Return top 10 common mistakes
    
    def _analyze_topic_performance(self,
                                  submissions: pd.DataFrame,
                                  tasks: Dict[str, Dict]) -> Dict[str, float]:
        """Analyze performance by topic"""
        topic_performance = defaultdict(lambda: {'correct': 0, 'total': 0})
        
        for _, row in submissions.iterrows():
            task_id = row.get('task_id')
            if task_id in tasks:
                topic = tasks[task_id].get('topic', 'Unknown')
                topic_performance[topic]['total'] += 1
                if row.get('is_correct'):
                    topic_performance[topic]['correct'] += 1
        
        # Calculate accuracy per topic
        result = {}
        for topic, counts in topic_performance.items():
            if counts['total'] > 0:
                result[topic] = counts['correct'] / counts['total']
        
        return result
    
    def _analyze_question_type_performance(self, submissions: pd.DataFrame) -> Dict[str, float]:
        """Analyze performance by question type"""
        q_types = ['keywords', 'center_sentence', 'center_paragraph', 'topic']
        performance = {}
        
        for q_type in q_types:
            type_subs = submissions[submissions['question_type'].str.contains(q_type, na=False)]
            if not type_subs.empty:
                accuracy = len(type_subs[type_subs['is_correct'] == True]) / len(type_subs)
                performance[q_type] = accuracy
        
        return performance
    
    def _calculate_engagement_score(self,
                                   submissions: pd.DataFrame,
                                   active_students: int,
                                   total_students: int) -> float:
        """Calculate overall engagement score"""
        if total_students == 0:
            return 0.0
        
        # Factors for engagement
        activity_rate = active_students / total_students
        
        # Submission frequency
        if 'timestamp' in submissions.columns:
            days_span = (pd.to_datetime(submissions['timestamp']).max() - 
                        pd.to_datetime(submissions['timestamp']).min()).days
            if days_span > 0:
                daily_submissions = len(submissions) / days_span
                frequency_score = min(1.0, daily_submissions / (total_students * 2))
            else:
                frequency_score = 0.5
        else:
            frequency_score = 0.5
        
        # Combine factors
        engagement_score = (activity_rate * 0.6 + frequency_score * 0.4)
        
        return engagement_score
    
    def identify_learning_patterns(self,
                                  submissions: pd.DataFrame,
                                  tasks: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Identify learning patterns and trends
        
        Returns:
            Dictionary with identified patterns
        """
        patterns = {
            'time_patterns': self._analyze_time_patterns(submissions),
            'difficulty_progression': self._analyze_difficulty_progression(submissions, tasks),
            'mistake_patterns': self._analyze_mistake_patterns(submissions),
            'learning_curves': self._analyze_learning_curves(submissions),
            'collaboration_patterns': self._analyze_collaboration_patterns(submissions)
        }
        
        return patterns
    
    def _analyze_time_patterns(self, submissions: pd.DataFrame) -> Dict[str, Any]:
        """Analyze when students are most active"""
        if 'timestamp' not in submissions.columns:
            return {}
        
        submissions['timestamp'] = pd.to_datetime(submissions['timestamp'])
        submissions['hour'] = submissions['timestamp'].dt.hour
        submissions['day_of_week'] = submissions['timestamp'].dt.dayofweek
        
        return {
            'peak_hours': submissions['hour'].mode().tolist(),
            'peak_days': submissions['day_of_week'].mode().tolist(),
            'avg_time_per_question': submissions.get('response_time', pd.Series()).mean()
        }
    
    def _analyze_difficulty_progression(self,
                                       submissions: pd.DataFrame,
                                       tasks: Dict[str, Dict]) -> Dict[str, Any]:
        """Analyze how students progress through difficulty levels"""
        difficulty_performance = defaultdict(list)
        
        for _, row in submissions.iterrows():
            task_id = row.get('task_id')
            if task_id in tasks:
                difficulty = tasks[task_id].get('difficulty', 'medium')
                difficulty_performance[difficulty].append(row.get('is_correct', False))
        
        progression = {}
        for difficulty, results in difficulty_performance.items():
            if results:
                progression[difficulty] = {
                    'accuracy': sum(results) / len(results),
                    'attempts': len(results)
                }
        
        return progression
    
    def _analyze_mistake_patterns(self, submissions: pd.DataFrame) -> Dict[str, Any]:
        """Analyze patterns in mistakes"""
        incorrect = submissions[submissions['is_correct'] == False]
        
        if incorrect.empty:
            return {}
        
        patterns = {
            'repeated_mistakes': self._find_repeated_mistakes(incorrect),
            'mistake_clusters': self._find_mistake_clusters(incorrect),
            'improvement_after_mistake': self._analyze_improvement_after_mistakes(submissions)
        }
        
        return patterns
    
    def _find_repeated_mistakes(self, incorrect: pd.DataFrame) -> List[Dict]:
        """Find tasks where students repeatedly make mistakes"""
        repeated = incorrect.groupby(['user_id', 'task_id']).size()
        repeated_mistakes = []
        
        for (user_id, task_id), count in repeated.items():
            if count >= 2:
                repeated_mistakes.append({
                    'user_id': user_id,
                    'task_id': task_id,
                    'repeat_count': int(count)
                })
        
        return repeated_mistakes
    
    def _find_mistake_clusters(self, incorrect: pd.DataFrame) -> List[Dict]:
        """Find clusters of mistakes (multiple students failing same task)"""
        task_failures = incorrect.groupby('task_id')['user_id'].nunique()
        clusters = []
        
        for task_id, student_count in task_failures.items():
            if student_count >= 3:
                clusters.append({
                    'task_id': task_id,
                    'affected_students': int(student_count)
                })
        
        return clusters
    
    def _analyze_improvement_after_mistakes(self, submissions: pd.DataFrame) -> float:
        """Analyze if students improve after making mistakes"""
        improvements = []
        
        for user_id in submissions['user_id'].unique():
            user_subs = submissions[submissions['user_id'] == user_id].sort_values('timestamp')
            
            for i in range(len(user_subs) - 1):
                if not user_subs.iloc[i]['is_correct'] and user_subs.iloc[i + 1]['is_correct']:
                    improvements.append(1)
                elif not user_subs.iloc[i]['is_correct'] and not user_subs.iloc[i + 1]['is_correct']:
                    improvements.append(0)
        
        return sum(improvements) / len(improvements) if improvements else 0.0
    
    def _analyze_learning_curves(self, submissions: pd.DataFrame) -> Dict[str, Any]:
        """Analyze learning curves for different student groups"""
        curves = {}
        
        # Group students by initial performance
        student_initial_performance = {}
        for user_id in submissions['user_id'].unique():
            user_subs = submissions[submissions['user_id'] == user_id].head(5)
            if not user_subs.empty:
                initial_acc = len(user_subs[user_subs['is_correct'] == True]) / len(user_subs)
                student_initial_performance[user_id] = initial_acc
        
        # Categorize students
        high_performers = [uid for uid, acc in student_initial_performance.items() if acc >= 0.8]
        medium_performers = [uid for uid, acc in student_initial_performance.items() if 0.5 <= acc < 0.8]
        low_performers = [uid for uid, acc in student_initial_performance.items() if acc < 0.5]
        
        # Calculate learning curves
        for group_name, group_ids in [('high', high_performers), 
                                       ('medium', medium_performers), 
                                       ('low', low_performers)]:
            if group_ids:
                group_subs = submissions[submissions['user_id'].isin(group_ids)]
                curve = self._calculate_learning_curve(group_subs)
                curves[group_name] = curve
        
        return curves
    
    def _calculate_learning_curve(self, submissions: pd.DataFrame) -> List[float]:
        """Calculate learning curve (accuracy over time)"""
        if submissions.empty:
            return []
        
        # Sort by timestamp and calculate cumulative accuracy
        sorted_subs = submissions.sort_values('timestamp') if 'timestamp' in submissions.columns else submissions
        
        window_size = max(10, len(sorted_subs) // 20)
        curve = []
        
        for i in range(0, len(sorted_subs), window_size):
            window = sorted_subs.iloc[i:i+window_size]
            if not window.empty:
                accuracy = len(window[window['is_correct'] == True]) / len(window)
                curve.append(accuracy)
        
        return curve
    
    def _analyze_collaboration_patterns(self, submissions: pd.DataFrame) -> Dict[str, Any]:
        """Analyze potential collaboration or cheating patterns"""
        patterns = {}
        
        if 'timestamp' not in submissions.columns:
            return patterns
        
        # Find submissions with very similar timestamps (potential collaboration)
        submissions['timestamp'] = pd.to_datetime(submissions['timestamp'])
        time_threshold = timedelta(minutes=5)
        
        suspicious_pairs = []
        for task_id in submissions['task_id'].unique():
            task_subs = submissions[submissions['task_id'] == task_id]
            
            for i in range(len(task_subs)):
                for j in range(i + 1, len(task_subs)):
                    time_diff = abs(task_subs.iloc[i]['timestamp'] - task_subs.iloc[j]['timestamp'])
                    if time_diff <= time_threshold:
                        user1 = task_subs.iloc[i]['user_id']
                        user2 = task_subs.iloc[j]['user_id']
                        if user1 != user2:
                            suspicious_pairs.append({
                                'user1': user1,
                                'user2': user2,
                                'task_id': task_id,
                                'time_diff_seconds': time_diff.total_seconds()
                            })
        
        patterns['suspicious_submissions'] = suspicious_pairs[:20]  # Limit to top 20
        
        return patterns
    
    def generate_recommendations(self,
                                student_metrics: PerformanceMetrics,
                                class_metrics: ClassMetrics,
                                patterns: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Generate personalized recommendations
        
        Returns:
            Dictionary with recommendations for students and teachers
        """
        recommendations = {
            'student': [],
            'teacher': [],
            'system': []
        }
        
        # Student recommendations based on performance
        if student_metrics:
            if student_metrics.keyword_accuracy < 0.6:
                recommendations['student'].append(
                    "키워드 식별 연습이 필요합니다. 문단의 핵심 단어를 찾는 훈련을 추천합니다."
                )
            
            if student_metrics.center_sentence_accuracy < 0.5:
                recommendations['student'].append(
                    "중심 문장 파악 능력을 향상시키세요. 각 문단의 주제문을 찾는 연습을 하세요."
                )
            
            if student_metrics.avg_similarity_score < 0.6:
                recommendations['student'].append(
                    "주제 서술 능력을 개선하세요. 핵심 내용을 간결하게 요약하는 연습이 필요합니다."
                )
            
            if student_metrics.improvement_trend < 0:
                recommendations['student'].append(
                    "최근 성적이 하락 추세입니다. 기초 개념을 다시 복습하는 것을 권장합니다."
                )
        
        # Teacher recommendations based on class metrics
        if class_metrics:
            if class_metrics.engagement_score < 0.5:
                recommendations['teacher'].append(
                    "학생 참여도가 낮습니다. 동기 부여 전략이나 흥미로운 콘텐츠 도입을 고려하세요."
                )
            
            if len(class_metrics.struggling_students) > class_metrics.total_students * 0.3:
                recommendations['teacher'].append(
                    f"{len(class_metrics.struggling_students)}명의 학생이 어려움을 겪고 있습니다. 보충 수업을 고려하세요."
                )
            
            if class_metrics.std_deviation > 0.25:
                recommendations['teacher'].append(
                    "학생 간 성취도 격차가 큽니다. 수준별 학습 자료 제공을 권장합니다."
                )
            
            # Recommendations based on common mistakes
            if class_metrics.common_mistakes:
                top_mistake = class_metrics.common_mistakes[0]
                recommendations['teacher'].append(
                    f"많은 학생이 '{top_mistake['question_type']}' 유형에서 실수합니다. 집중 지도가 필요합니다."
                )
        
        # System recommendations based on patterns
        if patterns:
            time_patterns = patterns.get('time_patterns', {})
            if time_patterns.get('avg_time_per_question', 0) > 300:  # 5 minutes
                recommendations['system'].append(
                    "평균 응답 시간이 길어 문제 난이도 조정이 필요할 수 있습니다."
                )
            
            difficulty_prog = patterns.get('difficulty_progression', {})
            if 'hard' in difficulty_prog and difficulty_prog['hard'].get('accuracy', 0) < 0.3:
                recommendations['system'].append(
                    "어려운 문제의 정답률이 매우 낮습니다. 난이도 재조정을 고려하세요."
                )
        
        return recommendations
    
    def export_analytics(self, 
                        student_metrics: Optional[PerformanceMetrics] = None,
                        class_metrics: Optional[ClassMetrics] = None,
                        patterns: Optional[Dict] = None,
                        recommendations: Optional[Dict] = None,
                        format: str = 'json') -> str:
        """
        Export analytics data in various formats
        
        Args:
            format: Export format ('json', 'csv', 'excel')
            
        Returns:
            Path to exported file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        export_data = {
            'timestamp': timestamp,
            'student_metrics': student_metrics.to_dict() if student_metrics else None,
            'class_metrics': class_metrics.to_dict() if class_metrics else None,
            'patterns': patterns,
            'recommendations': recommendations
        }
        
        if format == 'json':
            filepath = os.path.join(self.data_dir, 'exports', f'analytics_{timestamp}.json')
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        elif format == 'csv':
            filepath = os.path.join(self.data_dir, 'exports', f'analytics_{timestamp}.csv')
            # Flatten the data for CSV export
            flat_data = self._flatten_dict(export_data)
            df = pd.DataFrame([flat_data])
            df.to_csv(filepath, index=False)
        
        elif format == 'excel':
            filepath = os.path.join(self.data_dir, 'exports', f'analytics_{timestamp}.xlsx')
            with pd.ExcelWriter(filepath) as writer:
                if student_metrics:
                    pd.DataFrame([student_metrics.to_dict()]).to_excel(
                        writer, sheet_name='Student Metrics', index=False
                    )
                if class_metrics:
                    pd.DataFrame([class_metrics.to_dict()]).to_excel(
                        writer, sheet_name='Class Metrics', index=False
                    )
                if patterns:
                    pd.DataFrame([patterns]).to_excel(
                        writer, sheet_name='Patterns', index=False
                    )
                if recommendations:
                    pd.DataFrame(recommendations).to_excel(
                        writer, sheet_name='Recommendations', index=False
                    )
        
        return filepath
    
    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """Flatten nested dictionary for CSV export"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        return dict(items)


def main():
    """Main function for testing the analytics engine"""
    engine = LearningAnalyticsEngine()
    
    # Example usage
    print("Korean Reading Comprehension Learning Analytics System")
    print("=" * 60)
    
    # Load sample data
    submissions_file = "./grader/samples/submissions.csv"
    items_dir = "./generator/out"
    
    if os.path.exists(submissions_file):
        submissions = engine.load_submission_data(submissions_file)
        tasks = engine.load_task_items(items_dir)
        
        # Analyze individual student
        if not submissions.empty:
            sample_student = submissions['user_id'].iloc[0]
            student_metrics = engine.analyze_student_performance(sample_student, submissions, tasks)
            
            if student_metrics:
                print(f"\nStudent Performance Analysis for {sample_student}:")
                print(f"  Accuracy: {student_metrics.accuracy:.2%}")
                print(f"  Strengths: {', '.join(student_metrics.strengths)}")
                print(f"  Weaknesses: {', '.join(student_metrics.weaknesses)}")
            
            # Analyze class performance
            class_metrics = engine.analyze_class_performance("class_001", submissions, tasks)
            print(f"\nClass Performance Analysis:")
            print(f"  Total Students: {class_metrics.total_students}")
            print(f"  Average Accuracy: {class_metrics.avg_accuracy:.2%}")
            print(f"  Engagement Score: {class_metrics.engagement_score:.2%}")
            
            # Identify patterns
            patterns = engine.identify_learning_patterns(submissions, tasks)
            
            # Generate recommendations
            recommendations = engine.generate_recommendations(student_metrics, class_metrics, patterns)
            
            print("\nRecommendations:")
            for target, recs in recommendations.items():
                if recs:
                    print(f"  For {target}:")
                    for rec in recs:
                        print(f"    - {rec}")
            
            # Export results
            export_path = engine.export_analytics(
                student_metrics, class_metrics, patterns, recommendations
            )
            print(f"\nAnalytics exported to: {export_path}")
    else:
        print("Sample data not found. Please generate some data first.")


if __name__ == "__main__":
    main()