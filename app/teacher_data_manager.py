#!/usr/bin/env python3
"""
Teacher Dashboard Data Manager
- Student session tracking
- Progress monitoring
- Real-time data management
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import sqlite3
import threading
from pathlib import Path

class StudentStatus(Enum):
    ACTIVE = "active"          # Currently learning
    IDLE = "idle"             # Connected but not active
    STRUGGLING = "struggling"  # Needs help
    COMPLETED = "completed"    # Finished current task
    OFFLINE = "offline"        # Disconnected

class LearningDifficulty(Enum):
    EASY = "easy"
    MODERATE = "moderate"
    HARD = "hard"
    VERY_HARD = "very_hard"

@dataclass
class StudentSession:
    """Individual student learning session data"""
    student_id: str
    student_name: str
    class_id: str
    current_phase: int                    # 1-4 phase number
    current_task_id: str
    status: StudentStatus
    start_time: datetime
    last_activity: datetime
    
    # Progress tracking
    phase_scores: Dict[int, float] = field(default_factory=dict)  # Phase -> Score (0-1)
    phase_attempts: Dict[int, int] = field(default_factory=dict)  # Phase -> Attempt count
    phase_durations: Dict[int, int] = field(default_factory=dict) # Phase -> Seconds spent
    hints_used: Dict[int, int] = field(default_factory=dict)      # Phase -> Hint count
    
    # Current activity details
    current_question_start: Optional[datetime] = None
    difficulty_indicators: List[str] = field(default_factory=list)
    help_requested: bool = False
    consecutive_wrong: int = 0
    
    # Performance metrics
    total_time: int = 0                   # Total seconds in system
    mastery_level: float = 0.0           # Overall mastery 0-1
    learning_velocity: float = 0.0       # Questions per minute
    accuracy_trend: List[float] = field(default_factory=list)  # Last 10 accuracy scores
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        data['start_time'] = self.start_time.isoformat()
        data['last_activity'] = self.last_activity.isoformat()
        if self.current_question_start:
            data['current_question_start'] = self.current_question_start.isoformat()
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StudentSession':
        """Create StudentSession from dictionary"""
        # Convert ISO strings back to datetime
        data['start_time'] = datetime.fromisoformat(data['start_time'])
        data['last_activity'] = datetime.fromisoformat(data['last_activity'])
        if data.get('current_question_start'):
            data['current_question_start'] = datetime.fromisoformat(data['current_question_start'])
        data['status'] = StudentStatus(data['status'])
        return cls(**data)

@dataclass
class ClassAnalytics:
    """Class-wide learning analytics"""
    class_id: str
    class_name: str
    
    # Student counts by status
    active_students: int = 0
    struggling_students: int = 0
    completed_students: int = 0
    total_students: int = 0
    
    # Phase distribution
    phase_distribution: Dict[int, int] = field(default_factory=dict)  # Phase -> Student count
    
    # Performance metrics
    average_phase_scores: Dict[int, float] = field(default_factory=dict)
    fastest_completion_time: Optional[int] = None  # seconds
    slowest_completion_time: Optional[int] = None  # seconds
    
    # Common issues
    common_mistakes: List[Dict[str, Any]] = field(default_factory=list)
    help_hotspots: List[Dict[str, Any]] = field(default_factory=list)  # Questions needing most help

class TeacherDataManager:
    """
    Centralized data management for teacher dashboard
    - Tracks all student sessions
    - Provides real-time analytics
    - Manages class data
    """
    
    def __init__(self, db_path: str = "teacher_dashboard.db"):
        self.db_path = db_path
        self.sessions: Dict[str, StudentSession] = {}  # student_id -> StudentSession
        self.classes: Dict[str, ClassAnalytics] = {}   # class_id -> ClassAnalytics
        self.lock = threading.RLock()
        
        # Initialize database
        self._init_database()
        
        # Load existing sessions
        self._load_sessions()
        
        print("✅ Teacher Data Manager initialized")
    
    def _init_database(self):
        """Initialize SQLite database for persistent storage"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Student sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS student_sessions (
                    student_id TEXT PRIMARY KEY,
                    session_data TEXT NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Learning events log
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_data TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES student_sessions (student_id)
                )
            """)
            
            # Class management
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS classes (
                    class_id TEXT PRIMARY KEY,
                    class_name TEXT NOT NULL,
                    teacher_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    settings TEXT DEFAULT '{}'
                )
            """)
            
            conn.commit()
    
    def _load_sessions(self):
        """Load existing sessions from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT student_id, session_data FROM student_sessions")
            
            for student_id, session_json in cursor.fetchall():
                try:
                    session_data = json.loads(session_json)
                    session = StudentSession.from_dict(session_data)
                    self.sessions[student_id] = session
                except Exception as e:
                    print(f"Error loading session for {student_id}: {e}")
    
    def start_student_session(self, student_id: str, student_name: str, 
                            class_id: str, task_id: str) -> StudentSession:
        """Start a new learning session for a student"""
        with self.lock:
            now = datetime.now()
            
            session = StudentSession(
                student_id=student_id,
                student_name=student_name,
                class_id=class_id,
                current_phase=1,
                current_task_id=task_id,
                status=StudentStatus.ACTIVE,
                start_time=now,
                last_activity=now,
                current_question_start=now
            )
            
            self.sessions[student_id] = session
            self._save_session(session)
            self._log_event(student_id, "session_start", {"task_id": task_id})
            
            # Update class analytics
            self._update_class_analytics(class_id)
            
            print(f"📚 Started session for student {student_name} (ID: {student_id})")
            return session
    
    def update_student_progress(self, student_id: str, phase: int, score: float, 
                              response_data: Dict[str, Any] = None) -> bool:
        """Update student progress on a specific phase"""
        with self.lock:
            if student_id not in self.sessions:
                return False
            
            session = self.sessions[student_id]
            now = datetime.now()
            
            # Update phase progress
            session.phase_scores[phase] = score
            session.phase_attempts[phase] = session.phase_attempts.get(phase, 0) + 1
            
            # Calculate time spent on this phase
            if session.current_question_start:
                phase_time = int((now - session.current_question_start).total_seconds())
                session.phase_durations[phase] = session.phase_durations.get(phase, 0) + phase_time
            
            # Update accuracy trend
            session.accuracy_trend.append(score)
            if len(session.accuracy_trend) > 10:
                session.accuracy_trend.pop(0)
            
            # Determine if struggling
            if score < 0.5:
                session.consecutive_wrong += 1
                if session.consecutive_wrong >= 2:
                    session.status = StudentStatus.STRUGGLING
                    session.difficulty_indicators.append(f"Low score in Phase {phase}: {score:.2f}")
            else:
                session.consecutive_wrong = 0
                session.status = StudentStatus.ACTIVE
            
            # Update overall metrics
            session.last_activity = now
            session.total_time = int((now - session.start_time).total_seconds())
            session.mastery_level = sum(session.phase_scores.values()) / len(session.phase_scores) if session.phase_scores else 0
            
            # Check if should advance to next phase
            if score >= 0.75 and phase < 4:  # Advancement threshold
                session.current_phase = phase + 1
                session.current_question_start = now
            elif phase == 4 and score >= 0.75:
                session.status = StudentStatus.COMPLETED
                session.current_question_start = None
            
            # Save changes
            self._save_session(session)
            self._log_event(student_id, "progress_update", {
                "phase": phase,
                "score": score,
                "attempts": session.phase_attempts.get(phase, 0),
                "response_data": response_data or {}
            })
            
            # Update class analytics
            self._update_class_analytics(session.class_id)
            
            return True
    
    def request_help(self, student_id: str, help_type: str, context: Dict[str, Any] = None) -> bool:
        """Student requests help"""
        with self.lock:
            if student_id not in self.sessions:
                return False
            
            session = self.sessions[student_id]
            session.help_requested = True
            session.status = StudentStatus.STRUGGLING
            session.last_activity = datetime.now()
            
            self._save_session(session)
            self._log_event(student_id, "help_request", {
                "help_type": help_type,
                "context": context or {},
                "phase": session.current_phase
            })
            
            return True
    
    def use_hint(self, student_id: str, phase: int) -> bool:
        """Track hint usage"""
        with self.lock:
            if student_id not in self.sessions:
                return False
            
            session = self.sessions[student_id]
            session.hints_used[phase] = session.hints_used.get(phase, 0) + 1
            session.last_activity = datetime.now()
            
            self._save_session(session)
            self._log_event(student_id, "hint_used", {
                "phase": phase,
                "total_hints": session.hints_used[phase]
            })
            
            return True
    
    def get_class_overview(self, class_id: str) -> Dict[str, Any]:
        """Get comprehensive class overview for dashboard"""
        with self.lock:
            class_students = [s for s in self.sessions.values() if s.class_id == class_id]
            
            if not class_students:
                return {"class_id": class_id, "students": [], "analytics": {}}
            
            # Status distribution
            status_counts = {}
            for status in StudentStatus:
                status_counts[status.value] = len([s for s in class_students if s.status == status])
            
            # Phase distribution  
            phase_dist = {}
            for phase in range(1, 5):
                phase_dist[phase] = len([s for s in class_students if s.current_phase == phase])
            
            # Performance metrics
            phase_scores = {}
            for phase in range(1, 5):
                scores = [s.phase_scores.get(phase) for s in class_students if phase in s.phase_scores]
                if scores:
                    phase_scores[phase] = {
                        "average": sum(scores) / len(scores),
                        "min": min(scores),
                        "max": max(scores),
                        "count": len(scores)
                    }
            
            # Time analytics
            completion_times = [s.total_time for s in class_students if s.status == StudentStatus.COMPLETED]
            time_stats = {}
            if completion_times:
                time_stats = {
                    "average": sum(completion_times) / len(completion_times),
                    "min": min(completion_times),
                    "max": max(completion_times)
                }
            
            # Students needing attention
            struggling_students = [
                {
                    "student_id": s.student_id,
                    "student_name": s.student_name,
                    "phase": s.current_phase,
                    "issues": s.difficulty_indicators,
                    "consecutive_wrong": s.consecutive_wrong,
                    "help_requested": s.help_requested
                }
                for s in class_students 
                if s.status == StudentStatus.STRUGGLING or s.help_requested
            ]
            
            return {
                "class_id": class_id,
                "total_students": len(class_students),
                "status_distribution": status_counts,
                "phase_distribution": phase_dist,
                "phase_performance": phase_scores,
                "time_statistics": time_stats,
                "struggling_students": struggling_students,
                "last_updated": datetime.now().isoformat()
            }
    
    def get_student_detail(self, student_id: str) -> Dict[str, Any]:
        """Get detailed student information"""
        with self.lock:
            if student_id not in self.sessions:
                return None
            
            session = self.sessions[student_id]
            
            # Get recent learning events
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT event_type, event_data, timestamp 
                    FROM learning_events 
                    WHERE student_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 20
                """, (student_id,))
                
                recent_events = []
                for event_type, event_data_json, timestamp in cursor.fetchall():
                    try:
                        event_data = json.loads(event_data_json)
                        recent_events.append({
                            "type": event_type,
                            "data": event_data,
                            "timestamp": timestamp
                        })
                    except:
                        pass
            
            return {
                "session": session.to_dict(),
                "recent_events": recent_events,
                "recommendations": self._generate_student_recommendations(session)
            }
    
    def _generate_student_recommendations(self, session: StudentSession) -> List[Dict[str, str]]:
        """Generate recommendations for student based on performance"""
        recommendations = []
        
        # Check for struggling patterns
        if session.consecutive_wrong >= 2:
            recommendations.append({
                "type": "intervention",
                "message": f"{session.student_name}님이 연속으로 어려워하고 있습니다. 개별 도움이 필요할 수 있습니다.",
                "action": "provide_help"
            })
        
        # Check for excessive hint usage
        current_phase_hints = session.hints_used.get(session.current_phase, 0)
        if current_phase_hints > 3:
            recommendations.append({
                "type": "review",
                "message": "힌트를 많이 사용했습니다. 기본 개념 복습이 필요할 수 있습니다.",
                "action": "concept_review"
            })
        
        # Check for fast completion (might need challenge)
        avg_time_per_phase = session.total_time / max(session.current_phase, 1)
        if avg_time_per_phase < 60 and session.mastery_level > 0.9:  # Less than 1 minute per phase
            recommendations.append({
                "type": "challenge",
                "message": "매우 빠르게 완료하고 있습니다. 심화 학습을 제안해보세요.",
                "action": "advanced_content"
            })
        
        return recommendations
    
    def _save_session(self, session: StudentSession):
        """Save session to database"""
        session_json = json.dumps(session.to_dict(), ensure_ascii=False, indent=2)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO student_sessions (student_id, session_data)
                VALUES (?, ?)
            """, (session.student_id, session_json))
            conn.commit()
    
    def _log_event(self, student_id: str, event_type: str, event_data: Dict[str, Any]):
        """Log learning event"""
        event_json = json.dumps(event_data, ensure_ascii=False)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO learning_events (student_id, event_type, event_data)
                VALUES (?, ?, ?)
            """, (student_id, event_type, event_json))
            conn.commit()
    
    def _update_class_analytics(self, class_id: str):
        """Update class-wide analytics"""
        # This would update the ClassAnalytics object
        # Implementation details omitted for brevity
        pass
    
    def cleanup_inactive_sessions(self, inactive_threshold_minutes: int = 30):
        """Clean up inactive sessions"""
        with self.lock:
            now = datetime.now()
            threshold = timedelta(minutes=inactive_threshold_minutes)
            
            inactive_students = []
            for student_id, session in list(self.sessions.items()):
                # Only mark as offline if not already offline and actually inactive
                if (session.status != StudentStatus.OFFLINE and 
                    now - session.last_activity > threshold):
                    session.status = StudentStatus.OFFLINE
                    inactive_students.append(student_id)
            
            # Only print if we actually marked students offline
            if inactive_students:
                print(f"🧹 Marked {len(inactive_students)} students as offline")
            
            return inactive_students

# Global data manager instance
data_manager = TeacherDataManager()