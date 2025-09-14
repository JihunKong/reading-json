#!/usr/bin/env python3
"""
Enhanced Flask routes for the 4-Phase Korean Summary Learning System
With improved error handling, security, and Korean-language support
"""
import sys
import os
from pathlib import Path

# Use relative paths for deployment flexibility
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

from flask import Blueprint, render_template_string, request, jsonify, session
from datetime import datetime
import json
import random
import glob
import time
from pathlib import Path
from typing import Dict, Optional

from core.learning import (
    LearningPhaseController, EnhancedLearningTask, StudentResponse, 
    LearningPhase, ComponentType, Necessity
)

# Import security improvements
from app.security_improvements import (
    SecurityValidator, ErrorHandler, InputValidator, 
    rate_limit, secure_json_response, PerformanceMonitor
)

enhanced_learning_bp = Blueprint('enhanced_learning', __name__, url_prefix='/learning')

# Global learning controller
controller = LearningPhaseController()

def load_enhanced_tasks():
    """Load enhanced learning tasks with error handling"""
    tasks = []
    task_dir = BASE_DIR / 'data' / 'enhanced_tasks'
    
    if not task_dir.exists():
        print(f"⚠️ Enhanced tasks directory not found: {task_dir}")
        return tasks
    
    loaded_count = 0
    error_count = 0
    
    for task_file in task_dir.glob('*.json'):
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                task_data = json.load(f)
                
                # Validate task data structure
                if not isinstance(task_data, dict):
                    print(f"❌ Invalid task format in {task_file}: not a dictionary")
                    error_count += 1
                    continue
                
                # Sanitize task data
                sanitized_data = SecurityValidator.sanitize_input(task_data)
                
                task = EnhancedLearningTask.from_dict(sanitized_data)
                tasks.append(task)
                loaded_count += 1
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error in {task_file}: {e}")
            error_count += 1
        except Exception as e:
            print(f"❌ Failed to load enhanced task {task_file}: {e}")
            error_count += 1
    
    print(f"✅ Loaded {loaded_count} enhanced tasks, {error_count} errors")
    return tasks

# Load tasks at startup
enhanced_tasks = load_enhanced_tasks()

@enhanced_learning_bp.route('/')
@ErrorHandler.handle_exception
def learning_home():
    """Main learning interface"""
    return render_template_string(ENHANCED_LEARNING_TEMPLATE)

@enhanced_learning_bp.route('/get_task')
@ErrorHandler.handle_exception
@rate_limit(max_requests=50, window_seconds=60)  # Prevent abuse
def get_task():
    """Get a random enhanced learning task with security validation"""
    start_time = time.time()
    
    try:
        if not enhanced_tasks:
            return ErrorHandler.create_error_response('task_not_found', 
                '사용 가능한 학습 과제가 없습니다.', 404)
        
        # Get random task
        task = random.choice(enhanced_tasks)
        
        # Generate secure student ID if not exists
        if 'student_id' not in session:
            session['student_id'] = f'student_{datetime.now().strftime("%Y%m%d_%H%M%S")}_{random.randint(1000, 9999)}'
        
        # Store in session with security
        session['current_task_id'] = task.id
        session['current_phase'] = 1
        session['session_start_time'] = datetime.now().isoformat()
        
        # Prepare response data
        response_data = {
            'success': True,
            'task': {
                'id': task.id,
                'content': task.original_content['text'],
                'topic': task.original_content.get('topic', ''),
                'difficulty': task.original_content.get('difficulty', 'medium'),
                'sentence_count': len(task.sentence_analysis)
            },
            'student_id': session['student_id'],
            'timestamp': datetime.now().isoformat()
        }
        
        # Monitor performance
        execution_time = time.time() - start_time
        PerformanceMonitor.log_slow_query('get_task', execution_time, 0.5)
        
        return jsonify(response_data)
        
    except Exception as e:
        return ErrorHandler.create_error_response('server_error', None, 500)

@enhanced_learning_bp.route('/start_phase/<int:phase_num>')
@ErrorHandler.handle_exception
@rate_limit(max_requests=30, window_seconds=60)
def start_phase(phase_num: int):
    """Start a specific learning phase with enhanced validation"""
    start_time = time.time()
    
    try:
        # Validate phase number
        if not 1 <= phase_num <= 4:
            return ErrorHandler.create_error_response('validation_error', 
                '올바르지 않은 학습 단계입니다. (1-4단계만 사용 가능)', 400)
        
        # Get session data
        task_id = session.get('current_task_id')
        student_id = session.get('student_id')
        
        if not task_id or not student_id:
            return ErrorHandler.create_error_response('session_expired', 
                '세션이 만료되었습니다. 새로운 과제를 받아주세요.', 401)
        
        # Find task with security check
        task = None
        for t in enhanced_tasks:
            if t.id == task_id:
                task = t
                break
        
        if not task:
            return ErrorHandler.create_error_response('task_not_found', 
                '학습 과제를 찾을 수 없습니다.', 404)
        
        # Start appropriate phase
        try:
            if phase_num == 1:
                phase_data = controller.start_phase_1(task, student_id)
            elif phase_num == 2:
                phase_data = controller.start_phase_2(task, student_id)
            elif phase_num == 3:
                phase_data = controller.start_phase_3(task, student_id)
            elif phase_num == 4:
                phase_data = controller.start_phase_4(task, student_id)
        except Exception as e:
            return ErrorHandler.create_error_response('phase_error', 
                f'{phase_num}단계를 시작할 수 없습니다.', 500)
        
        # Update session
        session['current_phase'] = phase_num
        session['phase_start_time'] = datetime.now().isoformat()
        
        # Sanitize phase data
        sanitized_phase_data = SecurityValidator.sanitize_input(phase_data)
        
        response_data = {
            'success': True,
            'phase_data': sanitized_phase_data,
            'phase_num': phase_num,
            'timestamp': datetime.now().isoformat()
        }
        
        # Monitor performance
        execution_time = time.time() - start_time
        PerformanceMonitor.log_slow_query(f'start_phase_{phase_num}', execution_time, 1.0)
        
        return jsonify(response_data)
        
    except Exception as e:
        return ErrorHandler.create_error_response('server_error', None, 500)

@enhanced_learning_bp.route('/submit_phase/<int:phase_num>', methods=['POST'])
@ErrorHandler.handle_exception
@rate_limit(max_requests=20, window_seconds=60)
def submit_phase(phase_num: int):
    """Submit answer for a specific phase with enhanced security"""
    start_time = time.time()
    
    try:
        # Validate phase number
        if not 1 <= phase_num <= 4:
            return ErrorHandler.create_error_response('validation_error', 
                '올바르지 않은 학습 단계입니다.', 400)
        
        # Get session data
        task_id = session.get('current_task_id')
        student_id = session.get('student_id')
        
        if not task_id or not student_id:
            return ErrorHandler.create_error_response('session_expired', 
                '세션이 만료되었습니다.', 401)
        
        # Validate request data
        if not request.is_json:
            return ErrorHandler.create_error_response('invalid_input', 
                'JSON 형식의 데이터가 필요합니다.', 400)
        
        request_data = request.get_json()
        
        # Validate student response
        is_valid, error_message = InputValidator.validate_student_response(request_data)
        if not is_valid:
            return ErrorHandler.create_error_response('validation_error', error_message, 400)
        
        # Find task
        task = None
        for t in enhanced_tasks:
            if t.id == task_id:
                task = t
                break
        
        if not task:
            return ErrorHandler.create_error_response('task_not_found', 
                '학습 과제를 찾을 수 없습니다.', 404)
        
        # Get and sanitize response data
        response_data = SecurityValidator.sanitize_input(request_data.get('response_data', {}))
        
        # Map phase number to enum
        phase_mapping = {
            1: LearningPhase.COMPONENT_IDENTIFICATION,
            2: LearningPhase.NECESSITY_JUDGMENT,
            3: LearningPhase.GENERALIZATION,
            4: LearningPhase.THEME_RECONSTRUCTION
        }
        
        phase = phase_mapping[phase_num]
        
        # Create student response
        student_response = StudentResponse(
            student_id=student_id,
            task_id=task_id,
            phase=phase,
            timestamp=datetime.now().isoformat(),
            response_data=response_data
        )
        
        # Evaluate response
        try:
            evaluation_methods = {
                1: controller.evaluate_phase_1,
                2: controller.evaluate_phase_2,
                3: controller.evaluate_phase_3,
                4: controller.evaluate_phase_4
            }
            
            evaluation = evaluation_methods[phase_num](student_response, task)
            
        except Exception as e:
            return ErrorHandler.create_error_response('phase_error', 
                f'{phase_num}단계 평가 중 오류가 발생했습니다.', 500)
        
        # Update session with progress
        session[f'phase_{phase_num}_completed'] = True
        session[f'phase_{phase_num}_score'] = evaluation.get('score', 0)
        
        # Sanitize evaluation data
        sanitized_evaluation = SecurityValidator.sanitize_input(evaluation)
        
        response_data = {
            'success': True,
            'evaluation': sanitized_evaluation,
            'phase_num': phase_num,
            'next_phase_available': phase_num < 4,
            'timestamp': datetime.now().isoformat()
        }
        
        # Monitor performance
        execution_time = time.time() - start_time
        PerformanceMonitor.log_slow_query(f'submit_phase_{phase_num}', execution_time, 2.0)
        
        return jsonify(response_data)
        
    except Exception as e:
        return ErrorHandler.create_error_response('server_error', None, 500)

@enhanced_learning_bp.route('/get_progress')
@ErrorHandler.handle_exception
@rate_limit(max_requests=100, window_seconds=60)
def get_progress():
    """Get student progress with enhanced security"""
    try:
        student_id = session.get('student_id')
        task_id = session.get('current_task_id')
        
        if not student_id:
            return ErrorHandler.create_error_response('session_expired', 
                '세션이 만료되었습니다.', 401)
        
        # Calculate progress from session
        progress_data = {
            'student_id': student_id,
            'task_id': task_id,
            'current_phase': session.get('current_phase', 1),
            'phase_scores': {},
            'session_start_time': session.get('session_start_time'),
            'time_spent': 0,
            'hints_used': session.get('hints_used', 0),
            'attempts': session.get('attempts', 0),
            'mastery_progress': 0.0
        }
        
        # Calculate phase scores
        total_score = 0
        completed_phases = 0
        
        for phase in range(1, 5):
            phase_key = f'phase_{phase}_completed'
            score_key = f'phase_{phase}_score'
            
            if session.get(phase_key, False):
                score = session.get(score_key, 0)
                progress_data['phase_scores'][f'phase_{phase}'] = score
                total_score += score
                completed_phases += 1
        
        # Calculate mastery progress
        if completed_phases > 0:
            progress_data['mastery_progress'] = total_score / completed_phases
        
        # Calculate time spent
        if session.get('session_start_time'):
            try:
                start_time = datetime.fromisoformat(session['session_start_time'])
                time_spent = (datetime.now() - start_time).total_seconds()
                progress_data['time_spent'] = int(time_spent)
            except:
                progress_data['time_spent'] = 0
        
        # Sanitize progress data
        sanitized_progress = SecurityValidator.sanitize_input(progress_data)
        
        return jsonify({
            'success': True,
            'progress': sanitized_progress,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return ErrorHandler.create_error_response('server_error', None, 500)

@enhanced_learning_bp.route('/get_hint/<int:phase_num>')
@ErrorHandler.handle_exception
@rate_limit(max_requests=10, window_seconds=60)  # Limit hint requests
def get_hint(phase_num: int):
    """Get hint for current phase with rate limiting"""
    try:
        # Validate phase number
        if not 1 <= phase_num <= 4:
            return ErrorHandler.create_error_response('validation_error', 
                '올바르지 않은 학습 단계입니다.', 400)
        
        task_id = session.get('current_task_id')
        student_id = session.get('student_id')
        
        if not task_id or not student_id:
            return ErrorHandler.create_error_response('session_expired', 
                '세션이 만료되었습니다.', 401)
        
        # Find task
        task = None
        for t in enhanced_tasks:
            if t.id == task_id:
                task = t
                break
        
        if not task:
            return ErrorHandler.create_error_response('task_not_found', 
                '학습 과제를 찾을 수 없습니다.', 404)
        
        # Get phase-specific hints
        hints = task.learning_scaffolds.get(f'phase_{phase_num}_hints', [])
        
        if not hints:
            hints = [f'{phase_num}단계에 대한 기본 힌트입니다. 차근차근 문제를 읽어보세요.']
        
        # Track hint usage
        hints_used = session.get('hints_used', 0) + 1
        session['hints_used'] = hints_used
        
        # Limit excessive hint usage
        if hints_used > 10:
            return ErrorHandler.create_error_response('rate_limit', 
                '힌트 사용 횟수를 초과했습니다.', 429)
        
        # Sanitize hints
        sanitized_hints = SecurityValidator.sanitize_input(hints)
        
        return jsonify({
            'success': True,
            'hints': sanitized_hints,
            'hints_used': hints_used,
            'phase_num': phase_num,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return ErrorHandler.create_error_response('server_error', None, 500)

@enhanced_learning_bp.route('/reset_session', methods=['POST'])
@ErrorHandler.handle_exception
@rate_limit(max_requests=5, window_seconds=300)  # Limit session resets
def reset_session():
    """Reset learning session with security validation"""
    try:
        # Clear learning-related session data
        session_keys_to_clear = [
            'current_task_id', 'current_phase', 'session_start_time',
            'phase_start_time', 'hints_used', 'attempts'
        ]
        
        for key in session_keys_to_clear:
            session.pop(key, None)
        
        # Clear phase completion data
        for phase in range(1, 5):
            session.pop(f'phase_{phase}_completed', None)
            session.pop(f'phase_{phase}_score', None)
        
        return jsonify({
            'success': True,
            'message': '학습 세션이 초기화되었습니다.',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return ErrorHandler.create_error_response('server_error', None, 500)

@enhanced_learning_bp.route('/system_status')
@ErrorHandler.handle_exception
def system_status():
    """Get system status for monitoring"""
    try:
        # Get memory usage
        memory_stats = PerformanceMonitor.monitor_memory_usage()
        
        status_data = {
            'status': 'operational',
            'enhanced_tasks_loaded': len(enhanced_tasks),
            'memory_usage': memory_stats,
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0'
        }
        
        return jsonify(status_data)
        
    except Exception as e:
        return ErrorHandler.create_error_response('server_error', None, 500)

# Enhanced Learning Interface Template (truncated for brevity)
ENHANCED_LEARNING_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>4단계 한국어 요약 학습 시스템 (보안 강화)</title>
    <style>
        /* Enhanced CSS with security considerations */
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
            max-width: 1200px;
            width: 100%;
            text-align: center;
        }
        
        .security-badge {
            position: absolute;
            top: 10px;
            right: 10px;
            background: #48bb78;
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: bold;
        }
        
        .error-display {
            background: #fed7d7;
            border: 1px solid #f56565;
            color: #c53030;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            display: none;
        }
        
        .success-display {
            background: #c6f6d5;
            border: 1px solid #48bb78;
            color: #2f855a;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="security-badge">🔒 보안 강화</div>
        <h1>4단계 한국어 요약 학습 시스템</h1>
        <p>체계적이고 안전한 한국어 학습 환경</p>
        
        <div class="error-display" id="errorDisplay"></div>
        <div class="success-display" id="successDisplay"></div>
        
        <div id="learningContent">
            <button onclick="startLearning()" class="btn">학습 시작</button>
        </div>
    </div>
    
    <script>
        // Enhanced JavaScript with security measures
        function sanitizeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        function showError(message) {
            const errorDiv = document.getElementById('errorDisplay');
            errorDiv.textContent = sanitizeHtml(message);
            errorDiv.style.display = 'block';
            setTimeout(() => errorDiv.style.display = 'none', 5000);
        }
        
        function showSuccess(message) {
            const successDiv = document.getElementById('successDisplay');
            successDiv.textContent = sanitizeHtml(message);
            successDiv.style.display = 'block';
            setTimeout(() => successDiv.style.display = 'none', 3000);
        }
        
        async function startLearning() {
            try {
                const response = await fetch('/learning/get_task');
                const data = await response.json();
                
                if (data.success) {
                    showSuccess('학습 과제를 가져왔습니다.');
                    // Continue with learning interface
                } else {
                    showError(data.message || '오류가 발생했습니다.');
                }
            } catch (error) {
                showError('네트워크 오류가 발생했습니다.');
            }
        }
    </script>
</body>
</html>
"""