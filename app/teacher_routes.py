#!/usr/bin/env python3
"""
Teacher Dashboard Routes
- Main dashboard interface
- Real-time monitoring
- Class management
- Student intervention tools
"""

import sys
import os
import time
from pathlib import Path

# Use relative paths for deployment flexibility
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

from flask import Blueprint, render_template_string, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime, timedelta
import json
import csv
from io import StringIO, BytesIO
from typing import Dict, List, Optional, Any
import threading

from app.teacher_data_manager import data_manager, StudentStatus, LearningDifficulty
from app.analytics_engine import analytics_engine
from app.classroom_manager import classroom_manager
from app.intervention_system import intervention_system
from app.data_export_system import export_system

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

# Global SocketIO instance (will be initialized from main app)
socketio = None

def init_socketio(app_socketio):
    """Initialize SocketIO instance for real-time updates"""
    global socketio
    socketio = app_socketio
    
    # Register event handlers after socketio is initialized
    register_socketio_handlers()

# Teacher authentication decorator
def require_teacher_auth(f):
    """Decorator to require teacher authentication"""
    from functools import wraps
    
    @wraps(f)
    def wrapper(*args, **kwargs):
        # For demo purposes, simple teacher identification
        # In production, implement proper authentication
        teacher_id = request.args.get('teacher_id', 'teacher_demo')
        return f(*args, **kwargs)
    return wrapper

@teacher_bp.route('/')
@require_teacher_auth
def dashboard_home():
    """Main teacher dashboard"""
    return render_template_string(DASHBOARD_TEMPLATE)

@teacher_bp.route('/api/classes')
@require_teacher_auth
def get_classes():
    """Get list of classes for teacher"""
    # For demo, return sample classes
    classes = [
        {
            "class_id": "class_5a",
            "class_name": "5학년 A반",
            "student_count": 25,
            "active_session": True,
            "last_activity": datetime.now().isoformat()
        },
        {
            "class_id": "class_5b", 
            "class_name": "5학년 B반",
            "student_count": 23,
            "active_session": False,
            "last_activity": (datetime.now() - timedelta(hours=2)).isoformat()
        }
    ]
    
    return jsonify({
        "success": True,
        "classes": classes
    })

@teacher_bp.route('/api/class/<class_id>/overview')
@require_teacher_auth
def get_class_overview(class_id):
    """Get comprehensive class overview"""
    overview = data_manager.get_class_overview(class_id)
    return jsonify({
        "success": True,
        "data": overview
    })

@teacher_bp.route('/api/class/<class_id>/students')
@require_teacher_auth
def get_class_students(class_id):
    """Get detailed student list for class"""
    class_students = [
        session.to_dict() 
        for session in data_manager.sessions.values() 
        if session.class_id == class_id
    ]
    
    return jsonify({
        "success": True,
        "students": class_students
    })

@teacher_bp.route('/api/student/<student_id>/detail')
@require_teacher_auth
def get_student_detail(student_id):
    """Get detailed student information"""
    detail = data_manager.get_student_detail(student_id)
    
    if detail is None:
        return jsonify({
            "success": False,
            "message": "Student not found"
        }), 404
    
    return jsonify({
        "success": True,
        "data": detail
    })

@teacher_bp.route('/api/student/<student_id>/intervene', methods=['POST'])
@require_teacher_auth
def intervene_student(student_id):
    """Provide intervention for struggling student"""
    data = request.json
    intervention_type = data.get('type')  # 'hint', 'skip', 'reset', 'help_message'
    message = data.get('message', '')
    
    if intervention_type == 'hint':
        # Send hint to student
        if socketio:
            socketio.emit('teacher_hint', {
                'student_id': student_id,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }, room=f'student_{student_id}')
    
    elif intervention_type == 'skip':
        # Allow student to skip current question
        if socketio:
            socketio.emit('teacher_skip', {
                'student_id': student_id,
                'message': 'Teacher allowed you to skip this question',
                'timestamp': datetime.now().isoformat()
            }, room=f'student_{student_id}')
    
    elif intervention_type == 'help_message':
        # Send personalized help message
        if socketio:
            socketio.emit('teacher_message', {
                'student_id': student_id,
                'message': message,
                'type': 'help',
                'timestamp': datetime.now().isoformat()
            }, room=f'student_{student_id}')
    
    # Log intervention
    data_manager._log_event(student_id, "teacher_intervention", {
        "type": intervention_type,
        "message": message,
        "teacher_id": request.args.get('teacher_id', 'teacher_demo')
    })
    
    return jsonify({
        "success": True,
        "message": f"Intervention '{intervention_type}' sent to student"
    })

@teacher_bp.route('/api/class/<class_id>/analytics')
@require_teacher_auth
def get_class_analytics(class_id):
    """Get advanced analytics for class"""
    
    # Get all students in class
    class_students = [
        session for session in data_manager.sessions.values() 
        if session.class_id == class_id
    ]
    
    if not class_students:
        return jsonify({
            "success": True,
            "data": {
                "phase_progress": {},
                "time_analysis": {},
                "difficulty_patterns": [],
                "mastery_distribution": {}
            }
        })
    
    # Phase progress analysis
    phase_progress = {}
    for phase in range(1, 5):
        students_in_phase = [s for s in class_students if s.current_phase == phase]
        completed_phase = [s for s in class_students if phase in s.phase_scores]
        
        phase_progress[phase] = {
            "current_students": len(students_in_phase),
            "completed_students": len(completed_phase),
            "average_score": (
                sum(s.phase_scores[phase] for s in completed_phase) / len(completed_phase)
                if completed_phase else 0
            ),
            "average_attempts": (
                sum(s.phase_attempts.get(phase, 0) for s in class_students) / len(class_students)
                if class_students else 0
            )
        }
    
    # Time analysis
    phase_times = {}
    for phase in range(1, 5):
        times = [
            s.phase_durations.get(phase, 0) 
            for s in class_students 
            if phase in s.phase_durations
        ]
        if times:
            phase_times[phase] = {
                "average": sum(times) / len(times),
                "min": min(times),
                "max": max(times),
                "median": sorted(times)[len(times)//2] if times else 0
            }
    
    # Difficulty patterns
    difficulty_patterns = []
    for student in class_students:
        if student.consecutive_wrong >= 2 or student.status == StudentStatus.STRUGGLING:
            difficulty_patterns.append({
                "student_name": student.student_name,
                "phase": student.current_phase,
                "consecutive_wrong": student.consecutive_wrong,
                "indicators": student.difficulty_indicators,
                "help_requested": student.help_requested
            })
    
    # Mastery distribution
    mastery_levels = [s.mastery_level for s in class_students if s.mastery_level > 0]
    mastery_distribution = {
        "excellent": len([m for m in mastery_levels if m >= 0.9]),
        "good": len([m for m in mastery_levels if 0.7 <= m < 0.9]),
        "satisfactory": len([m for m in mastery_levels if 0.5 <= m < 0.7]),
        "needs_improvement": len([m for m in mastery_levels if m < 0.5]),
        "average": sum(mastery_levels) / len(mastery_levels) if mastery_levels else 0
    }
    
    return jsonify({
        "success": True,
        "data": {
            "phase_progress": phase_progress,
            "time_analysis": phase_times,
            "difficulty_patterns": difficulty_patterns,
            "mastery_distribution": mastery_distribution,
            "total_students": len(class_students),
            "generated_at": datetime.now().isoformat()
        }
    })

@teacher_bp.route('/api/export/class/<class_id>')
@require_teacher_auth
def export_class_data(class_id):
    """Export class data to CSV"""
    format_type = request.args.get('format', 'csv')  # csv or excel
    
    # Get class data
    class_students = [
        session for session in data_manager.sessions.values() 
        if session.class_id == class_id
    ]
    
    if format_type == 'csv':
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'Student ID', 'Student Name', 'Current Phase', 'Status',
            'Phase 1 Score', 'Phase 2 Score', 'Phase 3 Score', 'Phase 4 Score',
            'Total Time (min)', 'Mastery Level', 'Help Requests', 'Hints Used'
        ])
        
        # Data rows
        for student in class_students:
            total_hints = sum(student.hints_used.values())
            writer.writerow([
                student.student_id,
                student.student_name,
                student.current_phase,
                student.status.value,
                student.phase_scores.get(1, ''),
                student.phase_scores.get(2, ''),
                student.phase_scores.get(3, ''),
                student.phase_scores.get(4, ''),
                round(student.total_time / 60, 1),  # Convert to minutes
                round(student.mastery_level, 2),
                1 if student.help_requested else 0,
                total_hints
            ])
        
        output.seek(0)
        return output.getvalue(), 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename=class_{class_id}_data.csv'
        }
    
    return jsonify({"success": False, "message": "Unsupported format"}), 400

@teacher_bp.route('/api/settings', methods=['GET', 'POST'])
@require_teacher_auth
def dashboard_settings():
    """Get or update dashboard settings"""
    if request.method == 'GET':
        # Return current settings
        return jsonify({
            "success": True,
            "settings": {
                "refresh_interval": 5,  # seconds
                "auto_interventions": True,
                "notification_threshold": 2,  # consecutive wrong answers
                "time_warning_threshold": 300,  # 5 minutes per phase
                "mastery_threshold": 0.75
            }
        })
    
    elif request.method == 'POST':
        # Update settings
        new_settings = request.json
        # In production, save to database
        return jsonify({
            "success": True,
            "message": "Settings updated successfully"
        })

@teacher_bp.route('/api/class/<class_id>/advanced-analytics')
@require_teacher_auth
def get_advanced_analytics(class_id):
    """Get advanced learning analytics and insights"""
    try:
        analytics = analytics_engine.analyze_class(class_id)
        
        return jsonify({
            "success": True,
            "analytics": {
                "class_id": analytics.class_id,
                "timestamp": analytics.analysis_timestamp.isoformat(),
                "performance": {
                    "overall": analytics.overall_performance,
                    "trend": analytics.performance_trend,
                    "phase_completion": analytics.phase_completion_rates,
                    "learning_velocity": analytics.average_learning_velocity
                },
                "student_categories": {
                    "high_performers": len(analytics.high_performers),
                    "struggling": len(analytics.struggling_students),
                    "at_risk": len(analytics.at_risk_students),
                    "high_performer_ids": analytics.high_performers,
                    "struggling_ids": analytics.struggling_students,
                    "at_risk_ids": analytics.at_risk_students
                },
                "predictions": {
                    "completion_times": analytics.expected_completion_time,
                    "mastery_predictions": analytics.mastery_predictions
                },
                "insights": [
                    {
                        "type": insight.insight_type,
                        "confidence": insight.confidence,
                        "title": insight.title,
                        "description": insight.description,
                        "recommendations": insight.recommendations,
                        "severity": insight.severity,
                        "data": insight.data_points
                    } for insight in analytics.key_insights
                ],
                "interventions": analytics.intervention_recommendations
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to generate analytics: {str(e)}"
        }), 500

@teacher_bp.route('/api/student/<student_id>/learning-profile')
@require_teacher_auth  
def get_student_learning_profile(student_id):
    """Get detailed learning profile for individual student"""
    try:
        profile = analytics_engine.get_student_learning_profile(student_id)
        
        if profile is None:
            return jsonify({
                "success": False,
                "message": "Student not found"
            }), 404
        
        return jsonify({
            "success": True,
            "profile": profile
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to generate profile: {str(e)}"
        }), 500

@teacher_bp.route('/api/class/<class_id>/performance-report')
@require_teacher_auth
def generate_performance_report(class_id):
    """Generate comprehensive performance report"""
    try:
        report = analytics_engine.generate_performance_report(class_id)
        
        return jsonify({
            "success": True,
            "report": report
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to generate report: {str(e)}"
        }), 500

@teacher_bp.route('/api/class/<class_id>/roster')
@require_teacher_auth
def get_class_roster(class_id):
    """Get complete class roster with student details"""
    try:
        roster = classroom_manager.get_class_roster(class_id)
        
        return jsonify({
            "success": True,
            "class_id": class_id,
            "roster": roster,
            "total_students": len(roster)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to get roster: {str(e)}"
        }), 500

@teacher_bp.route('/api/class/<class_id>/assignments')
@require_teacher_auth
def get_class_assignments(class_id):
    """Get all assignments for a class"""
    try:
        assignments = [
            assignment for assignment in classroom_manager.assignments.values()
            if assignment.class_id == class_id
        ]
        
        assignment_list = []
        for assignment in assignments:
            progress = classroom_manager.get_assignment_progress(assignment.assignment_id)
            assignment_list.append({
                "assignment_id": assignment.assignment_id,
                "title": assignment.title,
                "description": assignment.description,
                "status": assignment.status.value,
                "created_at": assignment.created_at.isoformat(),
                "progress": progress["summary"] if progress else None
            })
        
        return jsonify({
            "success": True,
            "assignments": assignment_list
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to get assignments: {str(e)}"
        }), 500

@teacher_bp.route('/api/class/<class_id>/create-assignment', methods=['POST'])
@require_teacher_auth
def create_class_assignment(class_id):
    """Create a new assignment for the class"""
    try:
        data = request.json
        
        assignment = classroom_manager.create_assignment(
            class_id=class_id,
            title=data['title'],
            description=data['description'], 
            task_ids=data['task_ids'],
            difficulty_level=data.get('difficulty_level', 'medium'),
            phases_enabled=data.get('phases_enabled', [1, 2, 3, 4]),
            time_limit_minutes=data.get('time_limit_minutes'),
            max_attempts=data.get('max_attempts', 3)
        )
        
        # Assign to students if requested
        if data.get('assign_immediately', False):
            classroom_manager.assign_to_students(assignment.assignment_id)
        
        return jsonify({
            "success": True,
            "assignment": {
                "assignment_id": assignment.assignment_id,
                "title": assignment.title,
                "status": assignment.status.value
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to create assignment: {str(e)}"
        }), 500

@teacher_bp.route('/api/export/class/<class_id>/advanced', methods=['GET'])
@require_teacher_auth
def export_advanced_class_data(class_id):
    """Export comprehensive class data including analytics"""
    try:
        format_type = request.args.get('format', 'csv')
        include_analytics = request.args.get('include_analytics', 'true').lower() == 'true'
        
        if format_type == 'csv':
            # Get basic class data
            csv_data = classroom_manager.export_class_data(class_id, 'csv')
            
            if include_analytics:
                # Add analytics data as additional CSV
                analytics = analytics_engine.analyze_class(class_id)
                
                # Create comprehensive report
                import io
                output = io.StringIO()
                output.write("=== CLASS ROSTER ===\n")
                output.write(csv_data)
                output.write("\n=== ANALYTICS SUMMARY ===\n")
                
                # Add analytics summary
                writer = csv.writer(output)
                writer.writerow(['Metric', 'Value'])
                writer.writerow(['Overall Performance', f"{analytics.overall_performance:.2%}"])
                writer.writerow(['Performance Trend', analytics.performance_trend])
                writer.writerow(['Average Learning Velocity', f"{analytics.average_learning_velocity:.2f}"])
                writer.writerow(['High Performers', len(analytics.high_performers)])
                writer.writerow(['Struggling Students', len(analytics.struggling_students)])
                writer.writerow(['At Risk Students', len(analytics.at_risk_students)])
                
                output.write("\n=== PHASE COMPLETION RATES ===\n")
                writer.writerow(['Phase', 'Completion Rate'])
                for phase, rate in analytics.phase_completion_rates.items():
                    writer.writerow([f'Phase {phase}', f"{rate:.2%}"])
                
                csv_data = output.getvalue()
            
            return csv_data, 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': f'attachment; filename=class_{class_id}_advanced_export.csv'
            }
        
        elif format_type == 'json':
            # JSON export with full data
            export_data = {
                "class_data": classroom_manager.generate_class_report(class_id, "detailed"),
                "analytics": analytics_engine.analyze_class(class_id).__dict__ if include_analytics else None,
                "exported_at": datetime.now().isoformat(),
                "export_type": "advanced"
            }
            
            # Convert datetime objects and enums to strings for JSON serialization
            import json
            json_data = json.dumps(export_data, indent=2, default=str, ensure_ascii=False)
            
            return json_data, 200, {
                'Content-Type': 'application/json',
                'Content-Disposition': f'attachment; filename=class_{class_id}_advanced_export.json'
            }
        
        else:
            return jsonify({
                "success": False,
                "message": "Unsupported export format. Use 'csv' or 'json'"
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Export failed: {str(e)}"
        }), 500

# SocketIO event handlers will be registered after socketio is initialized
def register_socketio_handlers():
    """Register SocketIO event handlers after initialization"""
    if not socketio:
        return
    
    @socketio.on('teacher_join_monitoring')
    def on_teacher_join(data):
        """Teacher joins monitoring room"""
        class_id = data.get('class_id')
        if class_id:
            join_room(f'class_{class_id}_monitoring')
            emit('monitoring_joined', {
                'class_id': class_id,
                'message': f'Joined monitoring for {class_id}',
                'timestamp': datetime.now().isoformat()
            })
            print(f"👩‍🏫 Teacher joined monitoring room for class {class_id}")
    
    @socketio.on('teacher_leave_monitoring')
    def on_teacher_leave(data):
        """Teacher leaves monitoring room"""
        class_id = data.get('class_id')
        if class_id:
            leave_room(f'class_{class_id}_monitoring')
            emit('monitoring_left', {
                'class_id': class_id,
                'message': f'Left monitoring for {class_id}'
            })
    
    @socketio.on('student_progress_update') 
    def on_student_progress_update(data):
        """Forward student progress to teacher monitoring"""
        student_id = data.get('student_id')
        class_id = data.get('class_id')
        
        if class_id:
            # Send update to teachers monitoring this class
            socketio.emit('student_update', {
                'student_id': student_id,
                'class_id': class_id,
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'type': 'progress_update'
            }, room=f'class_{class_id}_monitoring')
    
    @socketio.on('request_student_help')
    def on_request_help(data):
        """Student requests help"""
        student_id = data.get('student_id')
        class_id = data.get('class_id')
        help_type = data.get('help_type', 'general')
        message = data.get('message', '')
        
        # Update data manager
        data_manager.request_help(student_id, help_type, data)
        
        # Notify teacher
        if class_id:
            socketio.emit('student_help_request', {
                'student_id': student_id,
                'class_id': class_id,
                'help_type': help_type,
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'urgency': 'high' if help_type == 'struggling' else 'medium'
            }, room=f'class_{class_id}_monitoring')
    
    @socketio.on('teacher_intervention_response')
    def on_intervention_response(data):
        """Handle teacher intervention response"""
        student_id = data.get('student_id')
        intervention_type = data.get('type')
        response = data.get('response')
        
        # Send to specific student
        socketio.emit('teacher_intervention', {
            'type': intervention_type,
            'response': response,
            'timestamp': datetime.now().isoformat()
        }, room=f'student_{student_id}')
        
        # Log the intervention
        data_manager._log_event(student_id, "teacher_intervention_sent", {
            'type': intervention_type,
            'response': response
        })
    
    print("✅ SocketIO event handlers registered")

# Real-time update background task
def send_periodic_updates():
    """Send periodic updates to teacher dashboards"""
    if not socketio:
        return
        
    def update_task():
        cleanup_interval = 60  # Start with 60 seconds for cleanup
        last_cleanup = 0
        cleanup_failures = 0
        
        while True:
            try:
                current_time = time.time()
                
                # Get all active classes
                active_classes = set()
                for session in data_manager.sessions.values():
                    if session.status != StudentStatus.OFFLINE:
                        active_classes.add(session.class_id)
                
                # Send updates for each class
                for class_id in active_classes:
                    overview = data_manager.get_class_overview(class_id)
                    socketio.emit('class_update', {
                        'class_id': class_id,
                        'data': overview
                    }, room=f'class_{class_id}_monitoring')
                
                # Clean up inactive sessions with exponential backoff
                if current_time - last_cleanup >= cleanup_interval:
                    try:
                        inactive_count = len(data_manager.cleanup_inactive_sessions(30))
                        last_cleanup = current_time
                        
                        # Reset interval on success
                        cleanup_failures = 0
                        cleanup_interval = 60  # Reset to 60 seconds
                        
                        # If no inactive students, increase interval to reduce load
                        if inactive_count == 0:
                            cleanup_interval = min(300, cleanup_interval * 1.5)  # Max 5 minutes
                            
                    except Exception as cleanup_error:
                        print(f"Error in session cleanup: {cleanup_error}")
                        cleanup_failures += 1
                        # Exponential backoff on failures
                        cleanup_interval = min(600, 60 * (2 ** cleanup_failures))  # Max 10 minutes
                
            except Exception as e:
                print(f"Error in periodic update task: {e}")
            
            # Wait 10 seconds before next update
            threading.Event().wait(10)
    
    # Start background thread
    thread = threading.Thread(target=update_task, daemon=True)
    thread.start()

# Dashboard HTML Template
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>교사 대시보드 - 4단계 한국어 요약 학습</title>
    
    <!-- Chart.js for visualizations -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
    
    <style>
        * { 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }
        
        body {
            font-family: '맑은 고딕', 'Malgun Gothic', sans-serif;
            background: #f5f7fa;
            line-height: 1.6;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            position: fixed;
            top: 0;
            width: 100%;
            z-index: 1000;
        }
        
        .header h1 {
            font-size: 1.8em;
            display: inline-block;
        }
        
        .header .controls {
            float: right;
            margin-top: 5px;
        }
        
        .header select, .header button {
            padding: 8px 15px;
            margin-left: 10px;
            border: none;
            border-radius: 5px;
            background: rgba(255,255,255,0.2);
            color: white;
            cursor: pointer;
        }
        
        .header button:hover {
            background: rgba(255,255,255,0.3);
        }
        
        .main-content {
            margin-top: 80px;
            padding: 20px;
            max-width: 1400px;
            margin-left: auto;
            margin-right: auto;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .dashboard-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 15px rgba(0,0,0,0.08);
            transition: transform 0.2s ease;
        }
        
        .dashboard-card:hover {
            transform: translateY(-2px);
        }
        
        .card-title {
            font-size: 1.1em;
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }
        
        .card-title .icon {
            margin-right: 10px;
            font-size: 1.3em;
        }
        
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #5a67d8;
            margin-bottom: 5px;
        }
        
        .metric-label {
            color: #718096;
            font-size: 0.9em;
        }
        
        .student-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .student-card {
            background: white;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            border-left: 4px solid #e2e8f0;
            position: relative;
        }
        
        .student-card.active {
            border-left-color: #48bb78;
        }
        
        .student-card.struggling {
            border-left-color: #f56565;
            animation: pulse-red 2s infinite;
        }
        
        .student-card.completed {
            border-left-color: #4299e1;
        }
        
        @keyframes pulse-red {
            0% { box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
            50% { box-shadow: 0 2px 20px rgba(245, 101, 101, 0.2); }
            100% { box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
        }
        
        .student-name {
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 8px;
        }
        
        .student-status {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            color: white;
            margin-bottom: 10px;
        }
        
        .status-active { background: #48bb78; }
        .status-struggling { background: #f56565; }
        .status-completed { background: #4299e1; }
        .status-idle { background: #a0aec0; }
        .status-offline { background: #e2e8f0; color: #4a5568; }
        
        .phase-progress {
            display: flex;
            gap: 5px;
            margin: 10px 0;
        }
        
        .phase-indicator {
            flex: 1;
            height: 6px;
            background: #e2e8f0;
            border-radius: 3px;
            position: relative;
        }
        
        .phase-indicator.current {
            background: linear-gradient(90deg, #48bb78 0%, #38a169 100%);
            animation: pulse-green 1.5s infinite;
        }
        
        .phase-indicator.completed {
            background: #4299e1;
        }
        
        @keyframes pulse-green {
            0% { opacity: 1; }
            50% { opacity: 0.6; }
            100% { opacity: 1; }
        }
        
        .student-actions {
            margin-top: 10px;
            display: flex;
            gap: 5px;
        }
        
        .action-btn {
            padding: 5px 10px;
            font-size: 0.8em;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .help-btn {
            background: #f6ad55;
            color: white;
        }
        
        .help-btn:hover {
            background: #ed8936;
        }
        
        .skip-btn {
            background: #a0aec0;
            color: white;
        }
        
        .skip-btn:hover {
            background: #718096;
        }
        
        .view-btn {
            background: #4299e1;
            color: white;
        }
        
        .view-btn:hover {
            background: #3182ce;
        }
        
        .charts-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 30px;
        }
        
        .chart-container {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 15px rgba(0,0,0,0.08);
        }
        
        .chart-title {
            font-size: 1.2em;
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 15px;
            text-align: center;
        }
        
        .intervention-panel {
            position: fixed;
            top: 80px;
            right: -350px;
            width: 350px;
            height: calc(100vh - 80px);
            background: white;
            box-shadow: -3px 0 15px rgba(0,0,0,0.1);
            transition: right 0.3s ease;
            padding: 20px;
            overflow-y: auto;
            z-index: 999;
        }
        
        .intervention-panel.open {
            right: 0;
        }
        
        .panel-header {
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e2e8f0;
        }
        
        .notification {
            position: fixed;
            top: 100px;
            right: 20px;
            background: #f56565;
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transform: translateX(400px);
            transition: transform 0.3s ease;
            z-index: 1001;
        }
        
        .notification.show {
            transform: translateX(0);
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @media (max-width: 768px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            
            .charts-section {
                grid-template-columns: 1fr;
            }
            
            .student-grid {
                grid-template-columns: 1fr;
            }
            
            .intervention-panel {
                width: 300px;
                right: -300px;
            }
        }
        
        .time-display {
            font-size: 0.9em;
            color: #718096;
            margin-bottom: 5px;
        }
        
        .score-display {
            font-size: 0.9em;
            color: #4a5568;
        }
        
        .alert-badge {
            position: absolute;
            top: -5px;
            right: -5px;
            width: 20px;
            height: 20px;
            background: #f56565;
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.7em;
            font-weight: bold;
        }
        
        /* Settings Modal Styles */
        .settings-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1500;
        }
        
        .modal-content {
            background: white;
            border-radius: 10px;
            width: 500px;
            max-width: 90vw;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        
        .modal-header {
            padding: 20px;
            border-bottom: 2px solid #e2e8f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .modal-header h3 {
            margin: 0;
            color: #2d3748;
        }
        
        .close-btn {
            background: none;
            border: none;
            font-size: 1.5em;
            cursor: pointer;
            color: #718096;
            padding: 5px;
        }
        
        .close-btn:hover {
            color: #f56565;
        }
        
        .modal-body {
            padding: 20px;
        }
        
        .setting-group {
            margin-bottom: 20px;
        }
        
        .setting-group label {
            display: block;
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 5px;
        }
        
        .setting-group input[type="number"],
        .setting-group input[type="text"] {
            width: 100%;
            padding: 8px 12px;
            border: 2px solid #e2e8f0;
            border-radius: 5px;
            font-size: 1em;
        }
        
        .setting-group input[type="checkbox"] {
            margin-right: 8px;
            transform: scale(1.2);
        }
        
        .modal-footer {
            padding: 20px;
            border-top: 2px solid #e2e8f0;
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            font-weight: bold;
            cursor: pointer;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3);
        }
        
        .btn-secondary {
            background: #e2e8f0;
            color: #4a5568;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            font-weight: bold;
            cursor: pointer;
        }
        
        .btn-secondary:hover {
            background: #cbd5e0;
        }
        
        /* Insights Container Styles */
        .insights-container {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            box-shadow: 0 2px 15px rgba(0,0,0,0.08);
        }
        
        .insights-container h3 {
            color: #2d3748;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .insight-card {
            background: #f7fafc;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid #e2e8f0;
            transition: all 0.3s ease;
        }
        
        .insight-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .insight-card.severity-info {
            border-left-color: #4299e1;
            background: #ebf8ff;
        }
        
        .insight-card.severity-warning {
            border-left-color: #f6ad55;
            background: #fffbeb;
        }
        
        .insight-card.severity-critical {
            border-left-color: #f56565;
            background: #fed7d7;
        }
        
        .insight-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .insight-header strong {
            color: #2d3748;
            font-size: 1.1em;
        }
        
        .confidence {
            background: rgba(72, 187, 120, 0.1);
            color: #38a169;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
        }
        
        .insight-description {
            color: #4a5568;
            margin-bottom: 10px;
            line-height: 1.5;
        }
        
        .insight-recommendations {
            list-style: none;
            padding: 0;
        }
        
        .insight-recommendations li {
            background: rgba(255,255,255,0.8);
            padding: 8px 12px;
            border-radius: 6px;
            margin: 5px 0;
            border-left: 3px solid #48bb78;
            color: #2d3748;
        }
        
        .insight-recommendations li:before {
            content: "💡 ";
            margin-right: 5px;
        }
        
        /* Enhanced notification styles */
        .notification.success {
            background: #48bb78;
        }
        
        .notification.error {
            background: #f56565;
        }
        
        .notification.critical {
            background: #f56565;
            animation: pulse-critical 2s infinite;
        }
        
        @keyframes pulse-critical {
            0% { box-shadow: 0 4px 15px rgba(245, 101, 101, 0.2); }
            50% { box-shadow: 0 8px 25px rgba(245, 101, 101, 0.4); }
            100% { box-shadow: 0 4px 15px rgba(245, 101, 101, 0.2); }
        }
        
        /* Additional chart container */
        .charts-advanced {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 20px;
        }
        
        /* Performance indicators */
        .performance-indicator {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            color: white;
            margin-left: 10px;
        }
        
        .performance-indicator.excellent {
            background: #48bb78;
        }
        
        .performance-indicator.good {
            background: #4299e1;
        }
        
        .performance-indicator.needs-improvement {
            background: #f6ad55;
        }
        
        .performance-indicator.poor {
            background: #f56565;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 교사 대시보드</h1>
        <div class="controls">
            <select id="classSelector" onchange="switchClass()">
                <option value="class_5a">5학년 A반</option>
                <option value="class_5b">5학년 B반</option>
            </select>
            <button onclick="exportData()">📥 데이터 내보내기</button>
            <button onclick="toggleSettings()">⚙️ 설정</button>
        </div>
    </div>
    
    <div class="main-content">
        <!-- Overview Cards -->
        <div class="dashboard-grid">
            <div class="dashboard-card">
                <div class="card-title">
                    <span class="icon">👥</span>
                    전체 학생 수
                </div>
                <div class="metric-value" id="totalStudents">-</div>
                <div class="metric-label">현재 접속 중</div>
            </div>
            
            <div class="dashboard-card">
                <div class="card-title">
                    <span class="icon">🎯</span>
                    학습 중
                </div>
                <div class="metric-value" id="activeStudents">-</div>
                <div class="metric-label">단계별 학습 진행</div>
            </div>
            
            <div class="dashboard-card">
                <div class="card-title">
                    <span class="icon">🆘</span>
                    도움 필요
                </div>
                <div class="metric-value" id="strugglingStudents">-</div>
                <div class="metric-label">개별 지도 필요</div>
            </div>
        </div>
        
        <!-- Student Monitoring Grid -->
        <div class="dashboard-card">
            <div class="card-title">
                <span class="icon">📚</span>
                실시간 학생 모니터링
                <div class="loading" id="loadingIndicator" style="margin-left: auto;"></div>
            </div>
            <div class="student-grid" id="studentGrid">
                <!-- Students will be populated here -->
            </div>
        </div>
        
        <!-- Analytics Charts -->
        <div class="charts-section">
            <div class="chart-container">
                <div class="chart-title">단계별 분포</div>
                <canvas id="phaseDistributionChart" width="400" height="300"></canvas>
            </div>
            
            <div class="chart-container">
                <div class="chart-title">성취도 분포</div>
                <canvas id="masteryDistributionChart" width="400" height="300"></canvas>
            </div>
        </div>
    </div>
    
    <!-- Intervention Panel -->
    <div class="intervention-panel" id="interventionPanel">
        <div class="panel-header">학생 개별 지도</div>
        <div id="interventionContent">
            학생을 선택하면 개별 지도 옵션이 표시됩니다.
        </div>
    </div>
    
    <!-- Notifications -->
    <div class="notification" id="notification">
        알림 메시지
    </div>

    <script>
        // Global variables
        let socket = null;
        let currentClass = 'class_5a';
        let phaseChart = null;
        let masteryChart = null;
        let performanceTrendChart = null;
        let interventionChart = null;
        let advancedAnalytics = null;
        let refreshInterval = null;
        
        // Settings
        let dashboardSettings = {
            refreshInterval: 5,
            autoInterventions: true,
            notificationThreshold: 2,
            timeWarningThreshold: 300,
            masteryThreshold: 0.75
        };
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            loadSettings();
            initializeSocketIO();
            loadClassData();
            loadAdvancedAnalytics();
            initializeCharts();
            
            // Start periodic updates based on settings
            startPeriodicUpdates();
        });
        
        function initializeSocketIO() {
            socket = io();
            
            socket.on('connect', function() {
                console.log('Connected to server');
                socket.emit('teacher_join_monitoring', {class_id: currentClass});
            });
            
            socket.on('student_update', function(data) {
                console.log('Student update received:', data);
                updateStudentCard(data);
            });
            
            socket.on('class_update', function(data) {
                console.log('Class update received:', data);
                if (data.class_id === currentClass) {
                    updateDashboard(data.data);
                }
            });
            
            socket.on('disconnect', function() {
                console.log('Disconnected from server');
                showNotification('서버 연결이 끊어졌습니다', 'error');
            });
        }
        
        function loadClassData() {
            fetch(`/teacher/api/class/${currentClass}/overview`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateDashboard(data.data);
                    }
                })
                .catch(error => {
                    console.error('Error loading class data:', error);
                });
        }
        
        function updateDashboard(data) {
            // Update overview metrics
            document.getElementById('totalStudents').textContent = data.total_students || 0;
            document.getElementById('activeStudents').textContent = 
                data.status_distribution?.active || 0;
            document.getElementById('strugglingStudents').textContent = 
                data.status_distribution?.struggling || 0;
            
            // Update student grid
            updateStudentGrid(data);
            
            // Update charts
            updateCharts(data);
            
            // Hide loading indicator
            document.getElementById('loadingIndicator').style.display = 'none';
        }
        
        function updateStudentGrid(data) {
            const grid = document.getElementById('studentGrid');
            
            // Load detailed student data
            fetch(`/teacher/api/class/${currentClass}/students`)
                .then(response => response.json())
                .then(studentData => {
                    if (studentData.success) {
                        renderStudentCards(studentData.students);
                    }
                })
                .catch(error => console.error('Error loading students:', error));
        }
        
        function renderStudentCards(students) {
            const grid = document.getElementById('studentGrid');
            grid.innerHTML = '';
            
            students.forEach(student => {
                const card = createStudentCard(student);
                grid.appendChild(card);
            });
        }
        
        function createStudentCard(student) {
            const card = document.createElement('div');
            card.className = `student-card ${student.status}`;
            card.id = `student-${student.student_id}`;
            
            // Calculate time spent
            const timeSpent = Math.round(student.total_time / 60); // minutes
            
            // Get current phase scores
            const phaseScores = student.phase_scores || {};
            const currentPhase = student.current_phase || 1;
            
            // Create phase indicators
            let phaseIndicators = '';
            for (let i = 1; i <= 4; i++) {
                let phaseClass = 'phase-indicator';
                if (i < currentPhase) phaseClass += ' completed';
                if (i === currentPhase) phaseClass += ' current';
                phaseIndicators += `<div class="${phaseClass}" title="Phase ${i}"></div>`;
            }
            
            // Status badge
            const statusLabels = {
                'active': '학습 중',
                'struggling': '도움 필요',
                'completed': '완료',
                'idle': '대기',
                'offline': '오프라인'
            };
            
            const statusLabel = statusLabels[student.status] || student.status;
            
            card.innerHTML = `
                <div class="student-name">${student.student_name}</div>
                <div class="student-status status-${student.status}">${statusLabel}</div>
                
                <div class="time-display">⏱️ ${timeSpent}분 소요</div>
                <div class="score-display">📊 평균: ${(student.mastery_level * 100).toFixed(0)}%</div>
                
                <div class="phase-progress">
                    ${phaseIndicators}
                </div>
                
                <div class="phase-info">
                    현재: ${currentPhase}단계 / 4단계
                </div>
                
                <div class="student-actions">
                    <button class="action-btn help-btn" onclick="sendHelp('${student.student_id}')">💡 힌트</button>
                    <button class="action-btn skip-btn" onclick="allowSkip('${student.student_id}')">⏭️ 넘기기</button>
                    <button class="action-btn view-btn" onclick="viewStudentDetail('${student.student_id}')">👀 자세히</button>
                </div>
                
                ${student.help_requested ? '<div class="alert-badge">!</div>' : ''}
            `;
            
            return card;
        }
        
        function initializeCharts() {
            // Phase Distribution Chart
            const phaseCtx = document.getElementById('phaseDistributionChart').getContext('2d');
            phaseChart = new Chart(phaseCtx, {
                type: 'bar',
                data: {
                    labels: ['1단계', '2단계', '3단계', '4단계'],
                    datasets: [{
                        label: '학생 수',
                        data: [0, 0, 0, 0],
                        backgroundColor: [
                            '#48bb78',
                            '#4299e1', 
                            '#f6ad55',
                            '#ed8936'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1
                            }
                        }
                    }
                }
            });
            
            // Mastery Distribution Chart
            const masteryCtx = document.getElementById('masteryDistributionChart').getContext('2d');
            masteryChart = new Chart(masteryCtx, {
                type: 'doughnut',
                data: {
                    labels: ['우수', '양호', '보통', '개선필요'],
                    datasets: [{
                        data: [0, 0, 0, 0],
                        backgroundColor: [
                            '#48bb78',
                            '#4299e1',
                            '#f6ad55', 
                            '#f56565'
                        ]
                    }]
                },
                options: {
                    responsive: true
                }
            });
        }
        
        function updateCharts(data) {
            // Update phase distribution chart
            if (phaseChart && data.phase_distribution) {
                const phaseData = [
                    data.phase_distribution[1] || 0,
                    data.phase_distribution[2] || 0,
                    data.phase_distribution[3] || 0,
                    data.phase_distribution[4] || 0
                ];
                phaseChart.data.datasets[0].data = phaseData;
                phaseChart.update();
            }
            
            // Update mastery chart (would need mastery distribution data)
            if (masteryChart) {
                // This would use actual mastery distribution data
                masteryChart.update();
            }
        }
        
        function sendHelp(studentId) {
            const message = prompt('학생에게 보낼 힌트 메시지를 입력하세요:');
            if (message) {
                fetch(`/teacher/api/student/${studentId}/intervene`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        type: 'hint',
                        message: message
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showNotification('힌트를 전송했습니다', 'success');
                    }
                })
                .catch(error => console.error('Error sending help:', error));
            }
        }
        
        function allowSkip(studentId) {
            if (confirm('이 학생이 현재 문제를 건너뛸 수 있도록 하시겠습니까?')) {
                fetch(`/teacher/api/student/${studentId}/intervene`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        type: 'skip',
                        message: 'Teacher allowed skip'
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showNotification('학생이 문제를 건너뛸 수 있습니다', 'success');
                    }
                })
                .catch(error => console.error('Error allowing skip:', error));
            }
        }
        
        function viewStudentDetail(studentId) {
            // Open intervention panel with student details
            fetch(`/teacher/api/student/${studentId}/detail`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStudentDetail(data.data);
                    }
                })
                .catch(error => console.error('Error loading student detail:', error));
        }
        
        function showStudentDetail(data) {
            const panel = document.getElementById('interventionPanel');
            const content = document.getElementById('interventionContent');
            
            const session = data.session;
            const events = data.recent_events || [];
            const recommendations = data.recommendations || [];
            
            content.innerHTML = `
                <h3>${session.student_name}</h3>
                <p><strong>현재 상태:</strong> ${session.status}</p>
                <p><strong>현재 단계:</strong> ${session.current_phase}/4</p>
                <p><strong>전체 시간:</strong> ${Math.round(session.total_time/60)}분</p>
                <p><strong>숙련도:</strong> ${(session.mastery_level*100).toFixed(0)}%</p>
                
                <h4 style="margin-top: 20px;">단계별 성과</h4>
                <div style="margin: 10px 0;">
                    ${Object.entries(session.phase_scores || {}).map(([phase, score]) => 
                        `<div>Phase ${phase}: ${(score*100).toFixed(0)}%</div>`
                    ).join('')}
                </div>
                
                <h4 style="margin-top: 20px;">추천 조치</h4>
                <div style="margin: 10px 0;">
                    ${recommendations.map(rec => 
                        `<div style="margin: 5px 0; padding: 8px; background: #f7fafc; border-radius: 4px;">
                            <strong>${rec.type}:</strong> ${rec.message}
                        </div>`
                    ).join('') || '추천 사항이 없습니다.'}
                </div>
                
                <div style="margin-top: 20px;">
                    <button class="action-btn help-btn" onclick="sendHelp('${session.student_id}')">💡 힌트 보내기</button>
                    <button class="action-btn skip-btn" onclick="allowSkip('${session.student_id}')">⏭️ 건너뛰기 허용</button>
                </div>
            `;
            
            panel.classList.add('open');
        }
        
        function switchClass() {
            const selector = document.getElementById('classSelector');
            currentClass = selector.value;
            
            // Join new monitoring room
            if (socket) {
                socket.emit('teacher_join_monitoring', {class_id: currentClass});
            }
            
            // Reload data
            loadClassData();
        }
        
        function exportData() {
            window.open(`/teacher/api/export/class/${currentClass}?format=csv`);
        }
        
        function loadSettings() {
            fetch('/teacher/api/settings')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        dashboardSettings = data.settings;
                    }
                })
                .catch(error => console.error('Error loading settings:', error));
        }
        
        function loadAdvancedAnalytics() {
            fetch(`/teacher/api/class/${currentClass}/advanced-analytics`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        advancedAnalytics = data.analytics;
                        updateAdvancedInsights(data.analytics);
                        updateInterventionRecommendations(data.analytics.interventions);
                    }
                })
                .catch(error => console.error('Error loading advanced analytics:', error));
        }
        
        function updateAdvancedInsights(analytics) {
            // Update insights display
            if (analytics.insights && analytics.insights.length > 0) {
                const insightsContainer = document.createElement('div');
                insightsContainer.className = 'insights-container';
                insightsContainer.innerHTML = '<h3>🔍 학습 인사이트</h3>';
                
                analytics.insights.forEach(insight => {
                    const insightCard = document.createElement('div');
                    insightCard.className = `insight-card severity-${insight.severity}`;
                    insightCard.innerHTML = `
                        <div class="insight-header">
                            <strong>${insight.title}</strong>
                            <span class="confidence">${(insight.confidence * 100).toFixed(0)}% 확신</span>
                        </div>
                        <div class="insight-description">${insight.description}</div>
                        <div class="insight-recommendations">
                            ${insight.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                        </div>
                    `;
                    insightsContainer.appendChild(insightCard);
                });
                
                // Add to main content
                const mainContent = document.querySelector('.main-content');
                const existingInsights = document.querySelector('.insights-container');
                if (existingInsights) {
                    existingInsights.replaceWith(insightsContainer);
                } else {
                    mainContent.appendChild(insightsContainer);
                }
            }
        }
        
        function updateInterventionRecommendations(interventions) {
            if (interventions && interventions.length > 0) {
                interventions.forEach(intervention => {
                    if (intervention.priority === 'high') {
                        showNotification(`긴급: ${intervention.title} - ${intervention.description}`, 'critical');
                        
                        // Auto-intervention if enabled
                        if (dashboardSettings.autoInterventions) {
                            // Could implement automatic actions here
                        }
                    }
                });
            }
        }
        
        function startPeriodicUpdates() {
            // Clear existing interval
            if (refreshInterval) {
                clearInterval(refreshInterval);
            }
            
            // Set new interval based on settings
            const intervalMs = dashboardSettings.refreshInterval * 1000;
            refreshInterval = setInterval(() => {
                loadClassData();
                loadAdvancedAnalytics();
            }, intervalMs);
        }
        
        function toggleSettings() {
            // Create settings modal
            const settingsModal = document.createElement('div');
            settingsModal.className = 'settings-modal';
            settingsModal.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>대시보드 설정</h3>
                        <button onclick="closeSettingsModal()" class="close-btn">✕</button>
                    </div>
                    <div class="modal-body">
                        <div class="setting-group">
                            <label>새로고침 간격 (초)</label>
                            <input type="number" id="refreshIntervalSetting" value="${dashboardSettings.refreshInterval}" min="1" max="60">
                        </div>
                        <div class="setting-group">
                            <label>
                                <input type="checkbox" id="autoInterventionsSetting" ${dashboardSettings.autoInterventions ? 'checked' : ''}>
                                자동 개입 활성화
                            </label>
                        </div>
                        <div class="setting-group">
                            <label>알림 임계값 (연속 오답 수)</label>
                            <input type="number" id="notificationThresholdSetting" value="${dashboardSettings.notificationThreshold}" min="1" max="5">
                        </div>
                        <div class="setting-group">
                            <label>시간 경고 임계값 (초)</label>
                            <input type="number" id="timeWarningThresholdSetting" value="${dashboardSettings.timeWarningThreshold}" min="60" max="1800">
                        </div>
                        <div class="setting-group">
                            <label>숙련도 임계값</label>
                            <input type="number" id="masteryThresholdSetting" value="${dashboardSettings.masteryThreshold}" min="0.1" max="1.0" step="0.05">
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button onclick="saveSettings()" class="btn-primary">저장</button>
                        <button onclick="closeSettingsModal()" class="btn-secondary">취소</button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(settingsModal);
        }
        
        function closeSettingsModal() {
            const modal = document.querySelector('.settings-modal');
            if (modal) {
                modal.remove();
            }
        }
        
        function saveSettings() {
            const newSettings = {
                refreshInterval: parseInt(document.getElementById('refreshIntervalSetting').value),
                autoInterventions: document.getElementById('autoInterventionsSetting').checked,
                notificationThreshold: parseInt(document.getElementById('notificationThresholdSetting').value),
                timeWarningThreshold: parseInt(document.getElementById('timeWarningThresholdSetting').value),
                masteryThreshold: parseFloat(document.getElementById('masteryThresholdSetting').value)
            };
            
            fetch('/teacher/api/settings', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(newSettings)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    dashboardSettings = newSettings;
                    startPeriodicUpdates(); // Restart with new interval
                    showNotification('설정이 저장되었습니다', 'success');
                    closeSettingsModal();
                }
            })
            .catch(error => {
                console.error('Error saving settings:', error);
                showNotification('설정 저장에 실패했습니다', 'error');
            });
        }
        
        function showNotification(message, type = 'info') {
            const notification = document.getElementById('notification');
            notification.textContent = message;
            notification.className = `notification show ${type}`;
            
            setTimeout(() => {
                notification.classList.remove('show');
            }, 3000);
        }
        
        // Close intervention panel when clicking outside
        document.addEventListener('click', function(event) {
            const panel = document.getElementById('interventionPanel');
            if (panel.classList.contains('open') && !panel.contains(event.target)) {
                // Check if click is on a view button
                if (!event.target.classList.contains('view-btn')) {
                    panel.classList.remove('open');
                }
            }
        });
        
        // Auto-refresh data every 30 seconds
        setInterval(() => {
            loadClassData();
        }, 30000);
    </script>
</body>
</html>
"""