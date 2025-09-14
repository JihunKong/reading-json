#!/usr/bin/env python3
"""
Simple Flask web interface for testing
"""

from flask import Flask, render_template, request, jsonify, session
import json
import os
import random
import glob
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'

class SimpleLearningSystem:
    def __init__(self):
        self.task_dir = "generator/out"
        self.tasks = self.load_tasks()
        
    def load_tasks(self):
        """Load all JSON task files"""
        tasks = []
        json_files = glob.glob(os.path.join(self.task_dir, "*.json"))
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    task = json.load(f)
                    task['file_path'] = file_path
                    tasks.append(task)
            except Exception as e:
                print(f"Failed to load {file_path}: {e}")
        
        print(f"Loaded {len(tasks)} tasks")
        return tasks
    
    def get_random_task(self):
        """Get a random task"""
        return random.choice(self.tasks) if self.tasks else None

learning_system = SimpleLearningSystem()

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'tasks_loaded': len(learning_system.tasks),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/')
def index():
    """Main page"""
    return render_template('study_enhanced.html')

@app.route('/api/get_task', methods=['POST'])
def get_task():
    """Get a random task"""
    task = learning_system.get_random_task()
    
    if task:
        # Initialize session tracking
        if 'user_id' not in session:
            session['user_id'] = os.urandom(16).hex()
            session['score'] = 0
            session['total'] = 0
        
        return jsonify({'success': True, 'task': task})
    
    return jsonify({'success': False, 'message': 'No tasks available'})

@app.route('/api/submit_answer', methods=['POST'])
def submit_answer():
    """Submit and evaluate answer"""
    data = request.json
    task_id = data.get('task_id')
    question_type = data.get('question_type')
    answer = data.get('answer')
    
    # Find the task
    current_task = None
    for task in learning_system.tasks:
        if task['id'] == task_id:
            current_task = task
            break
    
    if not current_task:
        return jsonify({'success': False, 'message': 'Task not found'})
    
    # Simple evaluation
    correct = False
    feedback = ""
    score = 0
    
    if question_type == 'keywords':
        q = current_task['q_keywords_mcq']
        correct = answer == q['answer_index']
        feedback = q['rationale'] if not correct else "정답입니다!"
        score = 1.0 if correct else 0.0
        
    elif question_type == 'center':
        if current_task['task_type'] == 'paragraph':
            q = current_task['q_center_sentence_mcq']
        else:
            q = current_task['q_center_paragraph_mcq']
        correct = answer == q.get('answer_idx', q.get('answer_index'))
        feedback = q['rationale'] if not correct else "정답입니다!"
        score = 1.0 if correct else 0.0
        
    elif question_type == 'topic':
        q = current_task['q_topic_free']
        # Simple keyword matching
        target = q['target_topic']
        score = 0.7 if any(word in answer for word in target.split()) else 0.3
        correct = score >= 0.68
        feedback = f"모범답안: {target}"
    
    # Update session
    session['score'] = session.get('score', 0) + (1 if correct else 0)
    session['total'] = session.get('total', 0) + 1
    
    return jsonify({
        'success': True,
        'correct': correct,
        'feedback': feedback,
        'score': score,
        'user_level': 0.5,
        'streak': 1
    })

@app.route('/api/get_progress')
def get_progress():
    """Get user progress"""
    return jsonify({
        'success': True,
        'progress': {
            'user_level': 0.5,
            'total_tasks': session.get('total', 0),
            'streak': 1,
            'score_history': [],
            'achievements': [],
            'weekly_stats': {'daily_tasks': [], 'daily_scores': [], 'dates': []}
        }
    })

@app.route('/api/get_analytics')
def get_analytics():
    """Get analytics (stub)"""
    return jsonify({
        'success': True,
        'analytics': {
            'performance_by_type': {},
            'difficulty_progression': [0.5],
            'time_analysis': {},
            'weakness_areas': [],
            'recommendations': ['계속 연습하세요!']
        }
    })

if __name__ == '__main__':
    print(f"Starting Korean Reading Comprehension System")
    print(f"Tasks loaded: {len(learning_system.tasks)}")
    if learning_system.tasks:
        print("Sample task IDs:", [t['id'] for t in learning_system.tasks[:3]])
    app.run(host='0.0.0.0', port=8080, debug=True)