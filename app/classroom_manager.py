#!/usr/bin/env python3
"""
Classroom Management System
- Class creation and management
- Student registration and grouping
- Assignment scheduling
- Progress tracking
"""

import json
import sqlite3
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import uuid
import hashlib

from app.teacher_data_manager import data_manager, StudentSession, StudentStatus

class AssignmentStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class StudentRole(Enum):
    STUDENT = "student"
    ASSISTANT = "assistant"  # Student helper
    OBSERVER = "observer"    # Parent/observer access

@dataclass
class ClassInfo:
    """Class information and settings"""
    class_id: str
    class_name: str
    teacher_id: str
    grade_level: str
    subject: str = "Korean Reading"
    
    # Settings
    max_students: int = 30
    session_timeout_minutes: int = 30
    allow_hint_usage: bool = True
    max_hints_per_phase: int = 3
    mastery_threshold: float = 0.75
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    description: str = ""
    tags: List[str] = field(default_factory=list)

@dataclass
class StudentProfile:
    """Student profile and settings"""
    student_id: str
    class_id: str
    student_name: str
    student_number: str  # School ID number
    
    # Personal settings
    preferred_difficulty: str = "medium"  # easy, medium, hard
    special_needs: List[str] = field(default_factory=list)
    learning_goals: List[str] = field(default_factory=list)
    
    # Permissions
    role: StudentRole = StudentRole.STUDENT
    can_skip_phases: bool = False
    extended_time: bool = False
    
    # Contact info
    parent_contact: str = ""
    notes: str = ""
    
    # Metadata
    enrolled_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    total_sessions: int = 0

@dataclass
class Assignment:
    """Learning assignment configuration"""
    assignment_id: str
    class_id: str
    title: str
    description: str
    
    # Content configuration
    task_ids: List[str]  # Specific tasks to use
    phases_enabled: List[int] = field(default_factory=lambda: [1, 2, 3, 4])
    difficulty_level: str = "medium"
    
    # Timing
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    time_limit_minutes: Optional[int] = None
    
    # Settings
    allow_retries: bool = True
    max_attempts: int = 3
    require_completion: bool = True
    enable_collaboration: bool = False
    
    # Status
    status: AssignmentStatus = AssignmentStatus.DRAFT
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""

class ClassroomManager:
    """
    Comprehensive classroom management system
    - Class and student management
    - Assignment creation and monitoring
    - Progress tracking and reporting
    """
    
    def __init__(self, db_path: str = "classroom_management.db"):
        self.db_path = db_path
        self.classes: Dict[str, ClassInfo] = {}
        self.students: Dict[str, StudentProfile] = {}
        self.assignments: Dict[str, Assignment] = {}
        
        # Initialize database
        self._init_database()
        self._load_data()
        
        print("✅ Classroom Manager initialized")
    
    def _init_database(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Classes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS classes (
                    class_id TEXT PRIMARY KEY,
                    class_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Students table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    student_id TEXT PRIMARY KEY,
                    class_id TEXT NOT NULL,
                    student_data TEXT NOT NULL,
                    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (class_id) REFERENCES classes (class_id)
                )
            """)
            
            # Assignments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assignments (
                    assignment_id TEXT PRIMARY KEY,
                    class_id TEXT NOT NULL,
                    assignment_data TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (class_id) REFERENCES classes (class_id)
                )
            """)
            
            # Student assignments (many-to-many)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS student_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    assignment_id TEXT NOT NULL,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    score REAL,
                    attempts INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'assigned',
                    FOREIGN KEY (student_id) REFERENCES students (student_id),
                    FOREIGN KEY (assignment_id) REFERENCES assignments (assignment_id),
                    UNIQUE(student_id, assignment_id)
                )
            """)
            
            conn.commit()
    
    def _load_data(self):
        """Load existing data from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Load classes
            cursor.execute("SELECT class_id, class_data FROM classes")
            for class_id, class_data_json in cursor.fetchall():
                try:
                    class_data = json.loads(class_data_json)
                    class_data['created_at'] = datetime.fromisoformat(class_data['created_at'])
                    class_data['last_modified'] = datetime.fromisoformat(class_data['last_modified'])
                    self.classes[class_id] = ClassInfo(**class_data)
                except Exception as e:
                    print(f"Error loading class {class_id}: {e}")
            
            # Load students
            cursor.execute("SELECT student_id, student_data FROM students")
            for student_id, student_data_json in cursor.fetchall():
                try:
                    student_data = json.loads(student_data_json)
                    student_data['enrolled_at'] = datetime.fromisoformat(student_data['enrolled_at'])
                    if student_data.get('last_login'):
                        student_data['last_login'] = datetime.fromisoformat(student_data['last_login'])
                    student_data['role'] = StudentRole(student_data['role'])
                    self.students[student_id] = StudentProfile(**student_data)
                except Exception as e:
                    print(f"Error loading student {student_id}: {e}")
            
            # Load assignments
            cursor.execute("SELECT assignment_id, assignment_data FROM assignments")
            for assignment_id, assignment_data_json in cursor.fetchall():
                try:
                    assignment_data = json.loads(assignment_data_json)
                    assignment_data['created_at'] = datetime.fromisoformat(assignment_data['created_at'])
                    if assignment_data.get('start_time'):
                        assignment_data['start_time'] = datetime.fromisoformat(assignment_data['start_time'])
                    if assignment_data.get('end_time'):
                        assignment_data['end_time'] = datetime.fromisoformat(assignment_data['end_time'])
                    assignment_data['status'] = AssignmentStatus(assignment_data['status'])
                    self.assignments[assignment_id] = Assignment(**assignment_data)
                except Exception as e:
                    print(f"Error loading assignment {assignment_id}: {e}")
    
    def create_class(self, class_name: str, teacher_id: str, grade_level: str,
                    **kwargs) -> ClassInfo:
        """Create a new class"""
        class_id = f"class_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        
        class_info = ClassInfo(
            class_id=class_id,
            class_name=class_name,
            teacher_id=teacher_id,
            grade_level=grade_level,
            **kwargs
        )
        
        self.classes[class_id] = class_info
        self._save_class(class_info)
        
        print(f"📚 Created class: {class_name} (ID: {class_id})")
        return class_info
    
    def add_student(self, class_id: str, student_name: str, student_number: str,
                   **kwargs) -> StudentProfile:
        """Add a student to a class"""
        if class_id not in self.classes:
            raise ValueError(f"Class {class_id} does not exist")
        
        # Generate student ID
        student_id = f"student_{class_id}_{student_number}_{uuid.uuid4().hex[:6]}"
        
        student_profile = StudentProfile(
            student_id=student_id,
            class_id=class_id,
            student_name=student_name,
            student_number=student_number,
            **kwargs
        )
        
        self.students[student_id] = student_profile
        self._save_student(student_profile)
        
        print(f"👤 Added student: {student_name} to class {class_id}")
        return student_profile
    
    def add_students_from_csv(self, class_id: str, csv_file_path: str) -> List[StudentProfile]:
        """Add multiple students from CSV file"""
        if class_id not in self.classes:
            raise ValueError(f"Class {class_id} does not exist")
        
        added_students = []
        
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                try:
                    student_profile = self.add_student(
                        class_id=class_id,
                        student_name=row['student_name'],
                        student_number=row['student_number'],
                        parent_contact=row.get('parent_contact', ''),
                        special_needs=row.get('special_needs', '').split(',') if row.get('special_needs') else [],
                        notes=row.get('notes', '')
                    )
                    added_students.append(student_profile)
                except Exception as e:
                    print(f"Error adding student from CSV row {row}: {e}")
        
        print(f"📥 Added {len(added_students)} students from CSV")
        return added_students
    
    def create_assignment(self, class_id: str, title: str, description: str,
                         task_ids: List[str], **kwargs) -> Assignment:
        """Create a new assignment"""
        if class_id not in self.classes:
            raise ValueError(f"Class {class_id} does not exist")
        
        assignment_id = f"assignment_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        
        assignment = Assignment(
            assignment_id=assignment_id,
            class_id=class_id,
            title=title,
            description=description,
            task_ids=task_ids,
            **kwargs
        )
        
        self.assignments[assignment_id] = assignment
        self._save_assignment(assignment)
        
        print(f"📋 Created assignment: {title} for class {class_id}")
        return assignment
    
    def assign_to_students(self, assignment_id: str, student_ids: List[str] = None) -> bool:
        """Assign assignment to students (all class students if student_ids not provided)"""
        if assignment_id not in self.assignments:
            raise ValueError(f"Assignment {assignment_id} does not exist")
        
        assignment = self.assignments[assignment_id]
        
        if student_ids is None:
            # Assign to all students in class
            student_ids = [
                student_id for student_id, student in self.students.items()
                if student.class_id == assignment.class_id
            ]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for student_id in student_ids:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO student_assignments 
                        (student_id, assignment_id, status)
                        VALUES (?, ?, 'assigned')
                    """, (student_id, assignment_id))
                except Exception as e:
                    print(f"Error assigning to student {student_id}: {e}")
            
            conn.commit()
        
        print(f"📤 Assigned {assignment.title} to {len(student_ids)} students")
        return True
    
    def start_assignment(self, assignment_id: str) -> bool:
        """Activate an assignment"""
        if assignment_id not in self.assignments:
            return False
        
        assignment = self.assignments[assignment_id]
        assignment.status = AssignmentStatus.ACTIVE
        assignment.start_time = datetime.now()
        
        self._save_assignment(assignment)
        
        print(f"▶️ Started assignment: {assignment.title}")
        return True
    
    def get_class_roster(self, class_id: str) -> List[Dict[str, Any]]:
        """Get complete class roster with student details"""
        if class_id not in self.classes:
            return []
        
        class_students = [
            student for student in self.students.values()
            if student.class_id == class_id
        ]
        
        roster = []
        for student in class_students:
            # Get current session if active
            current_session = data_manager.sessions.get(student.student_id)
            
            roster_entry = {
                "student_id": student.student_id,
                "student_name": student.student_name,
                "student_number": student.student_number,
                "role": student.role.value,
                "enrolled_at": student.enrolled_at.isoformat(),
                "last_login": student.last_login.isoformat() if student.last_login else None,
                "total_sessions": student.total_sessions,
                "special_needs": student.special_needs,
                "current_session": current_session.to_dict() if current_session else None,
                "parent_contact": student.parent_contact,
                "notes": student.notes
            }
            roster.append(roster_entry)
        
        return roster
    
    def get_assignment_progress(self, assignment_id: str) -> Dict[str, Any]:
        """Get detailed progress report for an assignment"""
        if assignment_id not in self.assignments:
            return None
        
        assignment = self.assignments[assignment_id]
        
        # Get student assignments from database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sa.student_id, sa.started_at, sa.completed_at, sa.score, 
                       sa.attempts, sa.status, s.student_data
                FROM student_assignments sa
                JOIN students s ON sa.student_id = s.student_id
                WHERE sa.assignment_id = ?
            """, (assignment_id,))
            
            student_progress = []
            for row in cursor.fetchall():
                student_id, started_at, completed_at, score, attempts, status, student_data_json = row
                
                try:
                    student_data = json.loads(student_data_json)
                    student_name = student_data['student_name']
                except:
                    student_name = "Unknown"
                
                student_progress.append({
                    "student_id": student_id,
                    "student_name": student_name,
                    "started_at": started_at,
                    "completed_at": completed_at,
                    "score": score,
                    "attempts": attempts,
                    "status": status
                })
        
        # Calculate summary statistics
        total_students = len(student_progress)
        completed = len([s for s in student_progress if s["status"] == "completed"])
        in_progress = len([s for s in student_progress if s["status"] == "started"])
        not_started = len([s for s in student_progress if s["status"] == "assigned"])
        
        avg_score = None
        scores = [s["score"] for s in student_progress if s["score"] is not None]
        if scores:
            avg_score = sum(scores) / len(scores)
        
        return {
            "assignment": {
                "assignment_id": assignment_id,
                "title": assignment.title,
                "description": assignment.description,
                "status": assignment.status.value,
                "start_time": assignment.start_time.isoformat() if assignment.start_time else None,
                "end_time": assignment.end_time.isoformat() if assignment.end_time else None
            },
            "summary": {
                "total_students": total_students,
                "completed": completed,
                "in_progress": in_progress,
                "not_started": not_started,
                "completion_rate": completed / total_students if total_students > 0 else 0,
                "average_score": avg_score
            },
            "student_progress": student_progress
        }
    
    def update_student_assignment_progress(self, student_id: str, assignment_id: str,
                                         score: float = None, status: str = None) -> bool:
        """Update student's progress on an assignment"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if status == "started":
                updates.append("started_at = ?")
                params.append(datetime.now().isoformat())
            elif status == "completed":
                updates.append("completed_at = ?")
                params.append(datetime.now().isoformat())
            
            if score is not None:
                updates.append("score = ?")
                params.append(score)
            
            if status:
                updates.append("status = ?")
                params.append(status)
            
            if updates:
                query = f"""
                    UPDATE student_assignments 
                    SET {', '.join(updates)}
                    WHERE student_id = ? AND assignment_id = ?
                """
                params.extend([student_id, assignment_id])
                
                cursor.execute(query, params)
                conn.commit()
                
                return cursor.rowcount > 0
        
        return False
    
    def get_student_assignments(self, student_id: str) -> List[Dict[str, Any]]:
        """Get all assignments for a student"""
        if student_id not in self.students:
            return []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sa.assignment_id, sa.started_at, sa.completed_at, sa.score, 
                       sa.attempts, sa.status, a.assignment_data
                FROM student_assignments sa
                JOIN assignments a ON sa.assignment_id = a.assignment_id
                WHERE sa.student_id = ?
                ORDER BY sa.started_at DESC
            """, (student_id,))
            
            assignments = []
            for row in cursor.fetchall():
                assignment_id, started_at, completed_at, score, attempts, status, assignment_data_json = row
                
                try:
                    assignment_data = json.loads(assignment_data_json)
                    assignments.append({
                        "assignment_id": assignment_id,
                        "title": assignment_data['title'],
                        "description": assignment_data['description'],
                        "started_at": started_at,
                        "completed_at": completed_at,
                        "score": score,
                        "attempts": attempts,
                        "status": status
                    })
                except Exception as e:
                    print(f"Error parsing assignment data: {e}")
            
            return assignments
    
    def generate_class_report(self, class_id: str, report_type: str = "summary") -> Dict[str, Any]:
        """Generate comprehensive class report"""
        if class_id not in self.classes:
            return None
        
        class_info = self.classes[class_id]
        class_students = [s for s in self.students.values() if s.class_id == class_id]
        
        report = {
            "class_info": {
                "class_id": class_id,
                "class_name": class_info.class_name,
                "teacher_id": class_info.teacher_id,
                "grade_level": class_info.grade_level,
                "created_at": class_info.created_at.isoformat()
            },
            "generated_at": datetime.now().isoformat(),
            "report_type": report_type
        }
        
        if report_type == "summary":
            report["summary"] = {
                "total_students": len(class_students),
                "active_students": len([s for s in class_students if data_manager.sessions.get(s.student_id)]),
                "total_assignments": len([a for a in self.assignments.values() if a.class_id == class_id]),
                "active_assignments": len([a for a in self.assignments.values() 
                                         if a.class_id == class_id and a.status == AssignmentStatus.ACTIVE])
            }
        
        elif report_type == "detailed":
            # Get detailed student information
            detailed_students = []
            for student in class_students:
                session = data_manager.sessions.get(student.student_id)
                assignments = self.get_student_assignments(student.student_id)
                
                detailed_students.append({
                    "student_profile": asdict(student),
                    "current_session": session.to_dict() if session else None,
                    "assignments": assignments
                })
            
            report["students"] = detailed_students
        
        return report
    
    def _save_class(self, class_info: ClassInfo):
        """Save class to database"""
        class_data = asdict(class_info)
        class_data['created_at'] = class_info.created_at.isoformat()
        class_data['last_modified'] = class_info.last_modified.isoformat()
        
        class_json = json.dumps(class_data, ensure_ascii=False, indent=2)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO classes (class_id, class_data)
                VALUES (?, ?)
            """, (class_info.class_id, class_json))
            conn.commit()
    
    def _save_student(self, student_profile: StudentProfile):
        """Save student to database"""
        student_data = asdict(student_profile)
        student_data['enrolled_at'] = student_profile.enrolled_at.isoformat()
        if student_profile.last_login:
            student_data['last_login'] = student_profile.last_login.isoformat()
        student_data['role'] = student_profile.role.value
        
        student_json = json.dumps(student_data, ensure_ascii=False, indent=2)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO students (student_id, class_id, student_data)
                VALUES (?, ?, ?)
            """, (student_profile.student_id, student_profile.class_id, student_json))
            conn.commit()
    
    def _save_assignment(self, assignment: Assignment):
        """Save assignment to database"""
        assignment_data = asdict(assignment)
        assignment_data['created_at'] = assignment.created_at.isoformat()
        if assignment.start_time:
            assignment_data['start_time'] = assignment.start_time.isoformat()
        if assignment.end_time:
            assignment_data['end_time'] = assignment.end_time.isoformat()
        assignment_data['status'] = assignment.status.value
        
        assignment_json = json.dumps(assignment_data, ensure_ascii=False, indent=2)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO assignments (assignment_id, class_id, assignment_data, status)
                VALUES (?, ?, ?, ?)
            """, (assignment.assignment_id, assignment.class_id, assignment_json, assignment.status.value))
            conn.commit()
    
    def export_class_data(self, class_id: str, format_type: str = "csv") -> str:
        """Export class data in various formats"""
        if class_id not in self.classes:
            raise ValueError(f"Class {class_id} not found")
        
        class_students = [s for s in self.students.values() if s.class_id == class_id]
        
        if format_type == "csv":
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                'Student ID', 'Name', 'Number', 'Role', 'Enrolled', 
                'Last Login', 'Total Sessions', 'Special Needs', 'Parent Contact'
            ])
            
            # Data
            for student in class_students:
                writer.writerow([
                    student.student_id,
                    student.student_name,
                    student.student_number,
                    student.role.value,
                    student.enrolled_at.strftime('%Y-%m-%d'),
                    student.last_login.strftime('%Y-%m-%d %H:%M') if student.last_login else '',
                    student.total_sessions,
                    '; '.join(student.special_needs),
                    student.parent_contact
                ])
            
            return output.getvalue()
        
        elif format_type == "json":
            export_data = {
                "class_info": asdict(self.classes[class_id]),
                "students": [asdict(student) for student in class_students],
                "exported_at": datetime.now().isoformat()
            }
            return json.dumps(export_data, ensure_ascii=False, indent=2, default=str)
        
        else:
            raise ValueError(f"Unsupported format: {format_type}")

# Global classroom manager instance
classroom_manager = ClassroomManager()