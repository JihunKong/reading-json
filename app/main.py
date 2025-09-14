#!/usr/bin/env python3
"""
Integrated Korean Reading Comprehension Learning System
- Legacy quiz system (backward compatibility)
- New 4-phase summary learning system
- Complete Teacher Dashboard with real-time monitoring
"""
import sys
import os
import time
sys.path.append('/Users/jihunkong/reading-json')

from flask import Flask, render_template_string, request, jsonify, redirect, url_for
from flask_socketio import SocketIO
import json
import random
import glob
from pathlib import Path
from datetime import datetime

# Import learning routes
from app.learning_routes import learning_bp

# Import teacher dashboard components
from app.teacher_routes import teacher_bp, init_socketio, send_periodic_updates
from app.teacher_data_manager import data_manager
from app.analytics_engine import analytics_engine
from app.classroom_manager import classroom_manager
from app.intervention_system import intervention_system
from app.data_export_system import export_system

# Import process manager for observability
from app.process_manager import process_observer, get_health_status, record_error, log_with_context

# Import admission control system
from app.admission_control import admission_controller, get_admission_metrics

# Import timeout budget and memory management
from app.timeout_budget import get_budget_metrics
from app.memory_management import get_memory_metrics

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['SECRET_KEY'] = app.secret_key

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global error handlers
@app.errorhandler(Exception)
def handle_exception(e):
    """Global exception handler with logging"""
    app.logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
    return jsonify({
        'success': False,
        'message': '시스템 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
        'error_code': 'INTERNAL_ERROR'
    }), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({
        'success': False,
        'message': '요청하신 페이지를 찾을 수 없습니다.',
        'error_code': 'NOT_FOUND'
    }), 404

@app.errorhandler(429)
def too_many_requests(error):
    """Handle admission control rejections with friendly messaging"""
    retry_after = getattr(error, 'retry_after', 5)
    return jsonify({
        'success': False,
        'message': '처리 대기 중입니다. 잠시 뒤 다시 시도해주세요.',
        'error_code': 'SERVICE_BUSY',
        'retry_after': retry_after
    }), 429, {'Retry-After': str(retry_after)}

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': '서버 내부 오류가 발생했습니다.',
        'error_code': 'SERVER_ERROR'
    }), 500

# Initialize SocketIO for teacher dashboard
init_socketio(socketio)

# Register blueprints
app.register_blueprint(learning_bp)
app.register_blueprint(teacher_bp)

# Legacy system (from enhanced_working.py)
class LegacyLearningSystem:
    def __init__(self):
        self.tasks = self.load_tasks()
        self.used_tasks = set()
    
    def load_tasks(self):
        tasks = []
        json_files = []
        json_files.extend(glob.glob("generator/parallel_sets/**/*.json", recursive=True))
        json_files.extend(glob.glob("generator/set_1/**/*.json", recursive=True))
        json_files.extend(glob.glob("generator/set_2/**/*.json", recursive=True))
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    task = json.load(f)
                    if 'id' not in task and 'task_id' in task:
                        task['id'] = task['task_id']
                    elif 'id' not in task:
                        task['id'] = os.path.basename(file_path).replace('.json', '')
                    tasks.append(task)
            except Exception as e:
                print(f"Failed to load {file_path}: {e}")
        
        print(f"Loaded {len(tasks)} legacy tasks")
        return tasks
    
    def get_random_task(self):
        available = [t for t in self.tasks if t['id'] not in self.used_tasks]
        if not available:
            self.used_tasks.clear()
            available = self.tasks
        
        if available:
            task = random.choice(available)
            self.used_tasks.add(task['id'])
            return task
        return None

# Initialize legacy system - will be set in main
legacy_system = None

# Home page template - system selector
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>한국어 독해 학습 시스템</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: '맑은 고딕', 'Malgun Gothic', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
            max-width: 800px;
            width: 100%;
            text-align: center;
        }
        
        h1 {
            color: #5a67d8;
            font-size: 2.5em;
            margin-bottom: 20px;
        }
        
        .subtitle {
            color: #718096;
            font-size: 1.2em;
            margin-bottom: 40px;
            line-height: 1.6;
        }
        
        .system-options {
            display: flex;
            gap: 30px;
            justify-content: center;
            flex-wrap: wrap;
        }
        
        .system-card {
            background: linear-gradient(135deg, #f6f8fb 0%, #e9ecef 100%);
            border: 2px solid #e2e8f0;
            border-radius: 15px;
            padding: 30px;
            flex: 1;
            min-width: 300px;
            max-width: 350px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            color: inherit;
        }
        
        .system-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 15px 30px rgba(102, 126, 234, 0.2);
            border-color: #667eea;
        }
        
        .system-icon {
            font-size: 3em;
            margin-bottom: 20px;
        }
        
        .system-title {
            font-size: 1.5em;
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 15px;
        }
        
        .system-description {
            color: #4a5568;
            line-height: 1.6;
            margin-bottom: 20px;
        }
        
        .system-features {
            text-align: left;
            margin-bottom: 20px;
        }
        
        .system-features li {
            color: #718096;
            margin: 8px 0;
        }
        
        .system-badge {
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white;
            padding: 6px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            display: inline-block;
        }
        
        .legacy-badge {
            background: linear-gradient(135deg, #f6ad55 0%, #ed8936 100%);
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
        }
        
        .footer {
            margin-top: 40px;
            color: #a0aec0;
            font-size: 0.9em;
        }
        
        @media (max-width: 768px) {
            .system-options {
                flex-direction: column;
                align-items: center;
            }
            
            h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 한국어 독해 학습 시스템</h1>
        <p class="subtitle">
            체계적이고 효과적인 한국어 독해 능력 향상을 위한<br>
            통합 학습 플랫폼입니다.
        </p>
        
        <div class="system-options">
            <!-- New 4-Phase Learning System -->
            <a href="/learning" class="system-card">
                <div class="system-icon">🎯</div>
                <div class="system-title">4단계 과정형 학습</div>
                <div class="system-badge">추천</div>
                <div class="system-description">
                    체계적인 요약 능력 개발을 위한 새로운 학습 방법입니다.
                    문장 성분부터 주제 재구성까지 단계적으로 학습합니다.
                </div>
                <ul class="system-features">
                    <li>🔍 1단계: 문장 성분 식별</li>
                    <li>⚖️ 2단계: 필수성 판단</li>
                    <li>🔄 3단계: 개념 일반화</li>
                    <li>🎨 4단계: 주제 재구성</li>
                </ul>
                <button class="btn">시작하기</button>
            </a>
            
            <!-- Teacher Dashboard -->
            <a href="/teacher" class="system-card">
                <div class="system-icon">📊</div>
                <div class="system-title">교사 대시보드</div>
                <div class="system-badge">신기능</div>
                <div class="system-description">
                    실시간 학생 모니터링 및 개별 지도를 위한
                    포괄적인 교사 관리 시스템입니다.
                </div>
                <ul class="system-features">
                    <li>👥 실시간 학생 모니터링</li>
                    <li>📈 성과 분석 및 예측</li>
                    <li>🎯 맞춤형 개입 지원</li>
                    <li>📋 학급 관리 및 보고서</li>
                </ul>
                <button class="btn">관리하기</button>
            </a>
            
            <!-- Legacy Quiz System -->
            <a href="/legacy" class="system-card">
                <div class="system-icon">📝</div>
                <div class="system-title">전통형 퀴즈 시스템</div>
                <div class="system-badge legacy-badge">호환성</div>
                <div class="system-description">
                    기존의 객관식/주관식 문제 형태로 구성된
                    전통적인 독해 평가 시스템입니다.
                </div>
                <ul class="system-features">
                    <li>🔤 핵심어 찾기</li>
                    <li>📖 중심 문장 선택</li>
                    <li>✍️ 주제 요약하기</li>
                    <li>⏱️ 시간 제한 모드</li>
                </ul>
                <button class="btn">시작하기</button>
            </a>
        </div>
        
        <div class="footer">
            <p>🎓 실제 교실 수업에 최적화된 한국어 독해 학습 시스템</p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    """Main system selector"""
    return render_template_string(HOME_TEMPLATE)

@app.route('/legacy')
def legacy_system():
    """Legacy quiz system interface"""
    # Import the HTML template from enhanced_working.py
    from enhanced_working import HTML_TEMPLATE
    return render_template_string(HTML_TEMPLATE)

@app.route('/legacy/get_task')
def legacy_get_task():
    """Legacy system task endpoint"""
    global legacy_system
    if legacy_system is None:
        return jsonify({'success': False, 'message': 'Legacy system not initialized'})
    
    task = legacy_system.get_random_task()
    if task:
        return jsonify({'success': True, 'task': task})
    return jsonify({'success': False, 'message': 'No tasks available'})

@app.route('/legacy/submit_answer', methods=['POST'])
def legacy_submit_answer():
    """Legacy system answer submission"""
    global legacy_system
    if legacy_system is None:
        return jsonify({'success': False, 'message': 'Legacy system not initialized'})
        
    # Import the logic from enhanced_working.py
    from enhanced_working import system as enhanced_system
    
    data = request.json
    task_id = data['task_id']
    question_type = data['question_type']
    answer = data['answer']
    is_timeout = data.get('is_timeout', False)
    
    # Find task
    task = None
    for t in legacy_system.tasks:
        if t['id'] == task_id:
            task = t
            break
    
    if not task:
        return jsonify({'success': False, 'message': 'Task not found'})
    
    correct = False
    correct_index = None
    
    if is_timeout:
        correct = False
        answer = None
    else:
        if question_type == 'keywords':
            q = task['q_keywords_mcq']
            original_correct_index = q.get('answer', q.get('answer_index', q.get('correct_index', 0)))
            correct_index = original_correct_index
            if correct_index > 0:
                correct_index = correct_index - 1
            correct = (answer == correct_index)
        
        elif question_type == 'center':
            if task['task_type'] == 'paragraph':
                q = task['q_center_sentence_mcq']
            else:
                q = task['q_center_paragraph_mcq']
            
            original_correct_index = q.get('answer', q.get('answer_idx', q.get('answer_index', 0)))
            correct_index = original_correct_index
            if correct_index > 0:
                correct_index = correct_index - 1
            correct = (answer == correct_index)
        
        elif question_type == 'topic':
            if answer:
                q = task['q_topic_free']
                target = q.get('answer', q.get('target_answer', q.get('target_topic', '')))
                similarity = enhanced_system.calculate_similarity(answer, target)
                correct = similarity >= 0.3
            else:
                correct = False
    
    # Generate explanation using enhanced_system logic
    explanation = enhanced_system.generate_explanation(task, question_type, answer, correct)
    
    return jsonify({
        'success': True,
        'correct': correct,
        'correct_index': correct_index,
        'explanation': explanation
    })

# Integration endpoints for teacher dashboard
@app.route('/api/student/session/start', methods=['POST'])
def start_student_session():
    """Start a new student session for teacher monitoring"""
    data = request.json
    
    session = data_manager.start_student_session(
        student_id=data['student_id'],
        student_name=data['student_name'],
        class_id=data['class_id'],
        task_id=data['task_id']
    )
    
    # Notify teacher dashboard
    if socketio:
        socketio.emit('student_update', {
            'student_id': session.student_id,
            'class_id': session.class_id,
            'status': session.status.value,
            'action': 'session_started'
        }, room=f'class_{session.class_id}_monitoring')
    
    return jsonify({
        'success': True,
        'session': session.to_dict()
    })

@app.route('/api/student/progress/update', methods=['POST'])
def update_student_progress():
    """Update student progress for teacher monitoring"""
    data = request.json
    
    success = data_manager.update_student_progress(
        student_id=data['student_id'],
        phase=data['phase'],
        score=data['score'],
        response_data=data.get('response_data', {})
    )
    
    if success and socketio:
        session = data_manager.sessions.get(data['student_id'])
        if session:
            socketio.emit('student_update', {
                'student_id': session.student_id,
                'class_id': session.class_id,
                'status': session.status.value,
                'phase': session.current_phase,
                'score': data['score'],
                'action': 'progress_updated'
            }, room=f'class_{session.class_id}_monitoring')
    
    return jsonify({
        'success': success,
        'message': 'Progress updated' if success else 'Failed to update progress'
    })

@app.route('/api/status')
def api_status():
    """Enhanced API status endpoint"""
    return jsonify({
        'status': 'running',
        'systems': {
            'legacy_tasks': len(legacy_system.tasks) if legacy_system else 0,
            'enhanced_learning': 'Available via /learning routes',
            'teacher_dashboard': 'Available via /teacher routes',
            'active_sessions': len(data_manager.sessions),
            'monitored_classes': len(set(s.class_id for s in data_manager.sessions.values()))
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
def health_check():
    """Comprehensive health check endpoint with observability"""
    try:
        correlation_id = process_observer.get_correlation_id()
        log_with_context('info', 'Health check requested', 'health', correlation_id)
        
        health_report = get_health_status()
        
        # Add admission control metrics
        admission_metrics = get_admission_metrics()
        health_report['admission_control'] = admission_metrics
        
        # Add timeout budget metrics
        budget_metrics = get_budget_metrics()
        health_report['timeout_budget'] = budget_metrics
        
        # Add memory management metrics
        memory_metrics = get_memory_metrics()
        health_report['memory_management'] = memory_metrics
        
        # Check if admission control is overloaded
        if admission_metrics['rejection_rate'] > 0.05:  # > 5% rejection rate
            health_report['warnings'] = health_report.get('warnings', [])
            health_report['warnings'].append(f"High rejection rate: {admission_metrics['rejection_rate']:.2%}")
        
        if admission_metrics['global_utilization'] > 0.8:  # > 80% utilization
            health_report['warnings'] = health_report.get('warnings', [])
            health_report['warnings'].append(f"High utilization: {admission_metrics['global_utilization']:.1%}")
        
        # Check memory management warnings
        if memory_metrics['utilization_pct'] > 80:  # > 80% memory usage
            health_report['warnings'] = health_report.get('warnings', [])
            health_report['warnings'].append(f"High memory usage: {memory_metrics['utilization_pct']:.1f}%")
        
        # Check timeout budget warnings  
        if budget_metrics['exhausted_count'] > 0:
            health_report['warnings'] = health_report.get('warnings', [])
            health_report['warnings'].append(f"Timeout budget exhausted for {budget_metrics['exhausted_count']} requests")
        
        # Determine HTTP status code based on health status
        status_code = 200
        if health_report['status'] == 'degraded':
            status_code = 200  # Still OK but degraded
        elif health_report['status'] == 'unhealthy':
            status_code = 503  # Service Unavailable
        elif health_report['status'] == 'critical':
            status_code = 503  # Service Unavailable
        
        return jsonify(health_report), status_code
        
    except Exception as e:
        record_error(e, 'health_endpoint')
        return jsonify({
            'service': 'korean-learning-system',
            'status': 'error',
            'message': 'Health check failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/health/ready')
def readiness_probe():
    """Readiness probe for Kubernetes/Docker deployments"""
    try:
        # Check critical dependencies
        checks = {
            'database': True,  # Would check DB connection
            'korean_analyzer': True,  # Would check NLP components
            'session_manager': len(data_manager.sessions) >= 0,
        }
        
        all_ready = all(checks.values())
        
        return jsonify({
            'ready': all_ready,
            'checks': checks,
            'timestamp': datetime.now().isoformat()
        }), 200 if all_ready else 503
        
    except Exception as e:
        record_error(e, 'readiness_probe')
        return jsonify({
            'ready': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/health/live')
def liveness_probe():
    """Liveness probe for Kubernetes/Docker deployments"""
    try:
        # Basic liveness check - is the process responsive?
        return jsonify({
            'alive': True,
            'uptime_seconds': time.time() - process_observer.start_time,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        record_error(e, 'liveness_probe')
        return jsonify({
            'alive': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/demo/setup')
def demo_setup():
    """Setup demo data for teacher dashboard"""
    try:
        # Create demo class
        demo_class = classroom_manager.create_class(
            class_name="5학년 A반 (데모)",
            teacher_id="teacher_demo",
            grade_level="5학년",
            description="교사 대시보드 데모용 학급"
        )
        
        # Add demo students
        demo_students = [
            {"name": "김영수", "number": "20240001"},
            {"name": "이민지", "number": "20240002"},
            {"name": "박준호", "number": "20240003"},
            {"name": "최서현", "number": "20240004"},
            {"name": "정다은", "number": "20240005"}
        ]
        
        for student_info in demo_students:
            student = classroom_manager.add_student(
                class_id=demo_class.class_id,
                student_name=student_info["name"],
                student_number=student_info["number"]
            )
            
            # Create demo session with random progress
            import random
            session = data_manager.start_student_session(
                student_id=student.student_id,
                student_name=student.student_name,
                class_id=demo_class.class_id,
                task_id="demo_task_001"
            )
            
            # Add some demo progress
            for phase in range(1, random.randint(2, 5)):
                score = random.uniform(0.4, 1.0)
                data_manager.update_student_progress(
                    student_id=student.student_id,
                    phase=phase,
                    score=score
                )
        
        return jsonify({
            'success': True,
            'message': 'Demo data created successfully',
            'class_id': demo_class.class_id,
            'class_name': demo_class.class_name,
            'students_created': len(demo_students)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Initialize legacy system  
    legacy_system = LegacyLearningSystem()
    
    # Make it available globally by updating the module-level variable
    globals()['legacy_system'] = legacy_system
    
    # Start background monitoring and update services
    send_periodic_updates()
    
    print("🚀 Integrated Korean Learning System Starting...")
    print(f"📊 Legacy tasks loaded: {len(legacy_system.tasks)}")
    print("🔗 4-Phase learning system available at /learning")
    print("📝 Legacy quiz system available at /legacy")  
    print("👩‍🏫 Teacher dashboard available at /teacher")
    print("🏠 Home page at /")
    print("📡 Real-time monitoring active")
    print("🎯 Educational interventions enabled")
    print("📈 Analytics engine ready")
    print("💾 Data export system ready")
    print("\n🌐 Server starting on http://localhost:8080")
    
    # Use SocketIO run instead of app.run for WebSocket support
    socketio.run(app, host='0.0.0.0', port=8080, debug=True, allow_unsafe_werkzeug=True)