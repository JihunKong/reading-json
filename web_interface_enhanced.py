#!/usr/bin/env python3
"""
Enhanced Korean Reading Comprehension Web Interface
Focus on factual reading and summarization strategies
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_session import Session
from flask_socketio import SocketIO, emit
import json
import os
import random
import glob
from datetime import datetime, timedelta
import redis
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
from typing import Dict, List, Optional, Tuple
import re
from collections import defaultdict
import numpy as np

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

Session(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Database connection
def get_db():
    """Get database connection"""
    return psycopg2.connect(
        os.environ.get('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/reading_db'),
        cursor_factory=RealDictCursor
    )

class EnhancedLearningSystem:
    """Enhanced learning system with summarization focus"""
    
    def __init__(self):
        self.task_dir = "generator/out"
        self.tasks = self.load_tasks()
        self.summarization_strategies = {
            'micro': self.micro_summarization,
            'macro': self.macro_summarization,
            'gist': self.gist_method,
            'reciprocal': self.reciprocal_teaching
        }
        
    def load_tasks(self) -> List[Dict]:
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
        
        return tasks
    
    def get_adaptive_task(self, user_level: float) -> Dict:
        """Get task based on adaptive difficulty"""
        # Calculate target difficulty based on user level
        if user_level < 0.4:
            target_difficulty = 'easy'
        elif user_level < 0.7:
            target_difficulty = 'medium'
        else:
            target_difficulty = 'hard'
        
        # Filter tasks by difficulty
        filtered = [t for t in self.tasks 
                   if t.get('metainfo', {}).get('difficulty') == target_difficulty]
        
        if not filtered:
            filtered = self.tasks
        
        return random.choice(filtered) if filtered else None
    
    def micro_summarization(self, text: str, max_words: int = 10) -> Dict:
        """Sentence-level summarization"""
        sentences = text.split('.')
        summaries = []
        
        for sentence in sentences:
            if sentence.strip():
                # Extract key words (simplified)
                words = sentence.strip().split()
                if len(words) <= max_words:
                    summaries.append(sentence.strip())
                else:
                    # Take first and last important words
                    important = words[:max_words//2] + words[-max_words//2:]
                    summaries.append(' '.join(important))
        
        return {
            'strategy': 'micro',
            'summaries': summaries,
            'feedback': '각 문장의 핵심을 추출했습니다.'
        }
    
    def macro_summarization(self, text: str) -> Dict:
        """Paragraph/article level summarization"""
        # Identify main idea patterns
        main_patterns = [
            r'가장 중요한',
            r'핵심은',
            r'결론적으로',
            r'요약하면'
        ]
        
        main_idea = None
        for pattern in main_patterns:
            match = re.search(pattern + r'[^.]+\.', text)
            if match:
                main_idea = match.group()
                break
        
        if not main_idea:
            # Take first and last sentences as fallback
            sentences = [s.strip() for s in text.split('.') if s.strip()]
            if sentences:
                main_idea = f"{sentences[0]}. {sentences[-1]}."
        
        return {
            'strategy': 'macro',
            'summary': main_idea,
            'structure': self._analyze_structure(text),
            'feedback': '글의 전체 구조를 파악했습니다.'
        }
    
    def gist_method(self, text: str) -> Dict:
        """GIST method implementation"""
        # Break text into segments
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        segments = []
        
        for i in range(0, len(sentences), 3):
            segment = '. '.join(sentences[i:i+3])
            if segment:
                segments.append({
                    'text': segment,
                    'gist': self._extract_gist(segment)
                })
        
        return {
            'strategy': 'gist',
            'segments': segments,
            'overall_gist': self._combine_gists([s['gist'] for s in segments]),
            'feedback': 'GIST 방법으로 핵심을 추출했습니다.'
        }
    
    def reciprocal_teaching(self, text: str) -> Dict:
        """Reciprocal teaching strategy"""
        strategies = {
            'predicting': self._generate_predictions(text),
            'questioning': self._generate_questions(text),
            'clarifying': self._identify_difficult_parts(text),
            'summarizing': self._create_summary(text)
        }
        
        return {
            'strategy': 'reciprocal',
            'components': strategies,
            'feedback': '상호교수법의 4가지 전략을 활용했습니다.'
        }
    
    def _analyze_structure(self, text: str) -> Dict:
        """Analyze text structure"""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        return {
            'introduction': sentences[0] if sentences else '',
            'body': sentences[1:-1] if len(sentences) > 2 else sentences[1:],
            'conclusion': sentences[-1] if len(sentences) > 1 else ''
        }
    
    def _extract_gist(self, segment: str) -> str:
        """Extract gist from segment"""
        # Simplified gist extraction
        words = segment.split()
        if len(words) <= 7:
            return segment
        return ' '.join(words[:7]) + '...'
    
    def _combine_gists(self, gists: List[str]) -> str:
        """Combine multiple gists"""
        return ' → '.join(gists)
    
    def _generate_predictions(self, text: str) -> List[str]:
        """Generate predictions based on text"""
        return [
            "다음 단락에서는 구체적인 예시가 나올 것입니다",
            "이 개념의 한계점이 논의될 것입니다"
        ]
    
    def _generate_questions(self, text: str) -> List[str]:
        """Generate questions about text"""
        return [
            "이 글의 주요 논점은 무엇인가요?",
            "저자가 전달하고자 하는 메시지는?",
            "제시된 근거는 충분한가요?"
        ]
    
    def _identify_difficult_parts(self, text: str) -> List[str]:
        """Identify difficult parts"""
        # Simplified - look for technical terms or complex sentences
        difficult = []
        sentences = text.split('.')
        for sent in sentences:
            if len(sent.split()) > 20:
                difficult.append(sent.strip())
        return difficult[:2] if difficult else ["어려운 부분이 없습니다"]
    
    def _create_summary(self, text: str) -> str:
        """Create summary"""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        if not sentences:
            return ""
        
        # Take first sentence and find most important middle sentence
        return f"{sentences[0]}. {sentences[len(sentences)//2] if len(sentences) > 2 else ''}"
    
    def calculate_reading_level(self, text: str) -> float:
        """Calculate text complexity level"""
        sentences = text.split('.')
        words = text.split()
        
        if not sentences or not words:
            return 0.5
        
        avg_sentence_length = len(words) / len(sentences)
        complex_words = sum(1 for w in words if len(w) > 6)
        
        # Simplified readability score
        complexity = (avg_sentence_length * 0.5 + complex_words * 0.5) / 100
        return min(max(complexity, 0.1), 1.0)

learning_system = EnhancedLearningSystem()

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/')
def index():
    """Main landing page"""
    return redirect(url_for('study'))

@app.route('/study')
def study():
    """Study interface"""
    if 'user_id' not in session:
        session['user_id'] = hashlib.md5(str(datetime.now()).encode()).hexdigest()
        session['user_level'] = 0.5
        session['score_history'] = []
        session['total_tasks'] = 0
        session['streak'] = 0
        session['last_activity'] = datetime.now().isoformat()
    
    return render_template('study_enhanced.html')

@app.route('/api/get_task', methods=['POST'])
def get_task():
    """Get adaptive task based on user level"""
    data = request.json
    strategy = data.get('strategy', 'adaptive')
    
    if strategy == 'adaptive':
        user_level = session.get('user_level', 0.5)
        task = learning_system.get_adaptive_task(user_level)
    else:
        # Random task
        task = random.choice(learning_system.tasks) if learning_system.tasks else None
    
    if task:
        session['current_task'] = task['id']
        session['task_start_time'] = datetime.now().isoformat()
        
        # Apply summarization strategy
        strategy_type = data.get('summarization_strategy', 'micro')
        if strategy_type in learning_system.summarization_strategies:
            text = task.get('paragraph', {}).get('text', '') if task['task_type'] == 'paragraph' else ' '.join(task.get('article', {}).get('paragraphs', []))
            summary_data = learning_system.summarization_strategies[strategy_type](text)
            task['summary_assistance'] = summary_data
        
        # Calculate reading complexity
        text = task.get('paragraph', {}).get('text', '') if task['task_type'] == 'paragraph' else ' '.join(task.get('article', {}).get('paragraphs', []))
        task['complexity_level'] = learning_system.calculate_reading_level(text)
        
        return jsonify({'success': True, 'task': task})
    
    return jsonify({'success': False, 'message': '사용 가능한 과제가 없습니다'})

@app.route('/api/submit_answer', methods=['POST'])
def submit_answer():
    """Submit and evaluate answer"""
    data = request.json
    task_id = data.get('task_id')
    question_type = data.get('question_type')
    answer = data.get('answer')
    
    # Load current task
    current_task = None
    for task in learning_system.tasks:
        if task['id'] == task_id:
            current_task = task
            break
    
    if not current_task:
        return jsonify({'success': False, 'message': '과제를 찾을 수 없습니다'})
    
    # Evaluate answer
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
        # Calculate similarity (simplified)
        target = q['target_topic']
        similarity = calculate_text_similarity(answer, target)
        score = similarity
        correct = similarity >= q['evaluation']['min_similarity']
        
        if correct:
            feedback = f"좋은 답변입니다! (유사도: {similarity:.2f})"
        else:
            feedback = f"더 구체적으로 작성해보세요. (유사도: {similarity:.2f})\n"
            feedback += "\n".join([f"• {guide}" for guide in q['feedback_guides']])
    
    # Update user level (adaptive algorithm)
    update_user_level(session, score)
    
    # Track in session
    if 'score_history' not in session:
        session['score_history'] = []
    
    session['score_history'].append({
        'task_id': task_id,
        'question_type': question_type,
        'score': score,
        'timestamp': datetime.now().isoformat()
    })
    
    # Update streak
    update_streak(session)
    
    # Save to database
    save_to_database(session['user_id'], task_id, question_type, answer, score)
    
    return jsonify({
        'success': True,
        'correct': correct,
        'feedback': feedback,
        'score': score,
        'user_level': session.get('user_level', 0.5),
        'streak': session.get('streak', 0)
    })

@app.route('/api/get_progress')
def get_progress():
    """Get user progress data"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '세션이 없습니다'})
    
    progress = {
        'user_level': session.get('user_level', 0.5),
        'total_tasks': session.get('total_tasks', 0),
        'streak': session.get('streak', 0),
        'score_history': session.get('score_history', [])[-10:],  # Last 10
        'achievements': calculate_achievements(session),
        'weekly_stats': get_weekly_stats(session['user_id'])
    }
    
    return jsonify({'success': True, 'progress': progress})

@app.route('/api/get_analytics')
def get_analytics():
    """Get detailed analytics"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '세션이 없습니다'})
    
    analytics = {
        'performance_by_type': analyze_performance_by_type(session),
        'difficulty_progression': analyze_difficulty_progression(session),
        'time_analysis': analyze_time_patterns(session),
        'weakness_areas': identify_weaknesses(session),
        'recommendations': generate_recommendations(session)
    }
    
    return jsonify({'success': True, 'analytics': analytics})

# WebSocket events for real-time features
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {'message': '학습 시스템에 연결되었습니다'})

@socketio.on('start_reading')
def handle_start_reading(data):
    """Track reading start"""
    task_id = data.get('task_id')
    emit('reading_started', {'task_id': task_id, 'timestamp': datetime.now().isoformat()})

@socketio.on('highlight_text')
def handle_highlight(data):
    """Handle text highlighting"""
    task_id = data.get('task_id')
    text = data.get('text')
    category = data.get('category')
    
    # Broadcast to other users in same session (for collaborative features)
    emit('text_highlighted', {
        'task_id': task_id,
        'text': text,
        'category': category,
        'user': session.get('user_id')
    }, broadcast=True)

# Helper functions
def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts"""
    # Simplified similarity calculation
    words1 = set(re.findall(r'[가-힣]+', text1.lower()))
    words2 = set(re.findall(r'[가-힣]+', text2.lower()))
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1 & words2
    union = words1 | words2
    
    return len(intersection) / len(union) if union else 0.0

def update_user_level(session_data: dict, score: float):
    """Update user level based on performance"""
    current_level = session_data.get('user_level', 0.5)
    
    # Adaptive algorithm with momentum
    learning_rate = 0.1
    momentum = 0.9
    
    # Calculate new level
    performance_delta = score - 0.7  # Target is 70% accuracy
    level_change = learning_rate * performance_delta
    
    # Apply momentum from recent history
    if 'level_momentum' in session_data:
        level_change = momentum * session_data['level_momentum'] + (1 - momentum) * level_change
    
    session_data['level_momentum'] = level_change
    new_level = current_level + level_change
    
    # Clamp between 0 and 1
    session_data['user_level'] = max(0.1, min(1.0, new_level))

def update_streak(session_data: dict):
    """Update learning streak"""
    last_activity = session_data.get('last_activity')
    current_time = datetime.now()
    
    if last_activity:
        last_time = datetime.fromisoformat(last_activity)
        time_diff = current_time - last_time
        
        if time_diff.days == 0:
            # Same day
            pass
        elif time_diff.days == 1:
            # Consecutive day
            session_data['streak'] = session_data.get('streak', 0) + 1
        else:
            # Streak broken
            session_data['streak'] = 1
    else:
        session_data['streak'] = 1
    
    session_data['last_activity'] = current_time.isoformat()

def calculate_achievements(session_data: dict) -> List[Dict]:
    """Calculate user achievements"""
    achievements = []
    
    total_tasks = session_data.get('total_tasks', 0)
    streak = session_data.get('streak', 0)
    user_level = session_data.get('user_level', 0.5)
    
    # Task-based achievements
    if total_tasks >= 10:
        achievements.append({'name': '첫 걸음', 'icon': '🌱', 'description': '10개 과제 완료'})
    if total_tasks >= 50:
        achievements.append({'name': '꾸준한 학습자', 'icon': '🌿', 'description': '50개 과제 완료'})
    if total_tasks >= 100:
        achievements.append({'name': '읽기 전문가', 'icon': '🌳', 'description': '100개 과제 완료'})
    
    # Streak achievements
    if streak >= 7:
        achievements.append({'name': '일주일 연속', 'icon': '🔥', 'description': '7일 연속 학습'})
    if streak >= 30:
        achievements.append({'name': '한 달 연속', 'icon': '💎', 'description': '30일 연속 학습'})
    
    # Level achievements
    if user_level >= 0.8:
        achievements.append({'name': '고급 학습자', 'icon': '🎓', 'description': '고급 수준 도달'})
    
    return achievements

def save_to_database(user_id: str, task_id: str, question_type: str, answer: str, score: float):
    """Save response to database"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO responses (user_id, task_id, question_type, answer, score, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, task_id, question_type, answer, score, datetime.now()))
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")

def get_weekly_stats(user_id: str) -> Dict:
    """Get weekly statistics"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as tasks,
                AVG(score) as avg_score
            FROM responses
            WHERE user_id = %s 
                AND created_at >= NOW() - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (user_id,))
        
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        return {
            'daily_tasks': [r['tasks'] for r in results],
            'daily_scores': [float(r['avg_score']) if r['avg_score'] else 0 for r in results],
            'dates': [r['date'].isoformat() for r in results]
        }
    except Exception as e:
        print(f"Database error: {e}")
        return {'daily_tasks': [], 'daily_scores': [], 'dates': []}

def analyze_performance_by_type(session_data: dict) -> Dict:
    """Analyze performance by question type"""
    history = session_data.get('score_history', [])
    
    performance = defaultdict(lambda: {'total': 0, 'correct': 0})
    
    for item in history:
        q_type = item['question_type']
        performance[q_type]['total'] += 1
        if item['score'] >= 0.7:
            performance[q_type]['correct'] += 1
    
    return {
        q_type: {
            'accuracy': data['correct'] / data['total'] if data['total'] > 0 else 0,
            'total': data['total']
        }
        for q_type, data in performance.items()
    }

def analyze_difficulty_progression(session_data: dict) -> List[float]:
    """Analyze difficulty progression"""
    # Return user level history (simplified)
    return [0.5, 0.55, 0.6, 0.58, 0.65, 0.7, session_data.get('user_level', 0.5)]

def analyze_time_patterns(session_data: dict) -> Dict:
    """Analyze time patterns"""
    # Simplified time analysis
    return {
        'average_time_per_task': 180,  # 3 minutes
        'best_performance_time': '14:00-16:00',
        'total_study_time': len(session_data.get('score_history', [])) * 3
    }

def identify_weaknesses(session_data: dict) -> List[str]:
    """Identify weakness areas"""
    performance = analyze_performance_by_type(session_data)
    
    weaknesses = []
    for q_type, data in performance.items():
        if data['accuracy'] < 0.6:
            if q_type == 'keywords':
                weaknesses.append('핵심어 파악')
            elif q_type == 'center':
                weaknesses.append('중심 문장/문단 파악')
            elif q_type == 'topic':
                weaknesses.append('주제 요약')
    
    return weaknesses if weaknesses else ['현재 약점이 발견되지 않았습니다']

def generate_recommendations(session_data: dict) -> List[str]:
    """Generate personalized recommendations"""
    recommendations = []
    
    user_level = session_data.get('user_level', 0.5)
    weaknesses = identify_weaknesses(session_data)
    
    if user_level < 0.4:
        recommendations.append('쉬운 난이도의 과제를 더 연습하세요')
    elif user_level > 0.8:
        recommendations.append('도전적인 고급 과제에 도전해보세요')
    
    if '핵심어 파악' in weaknesses:
        recommendations.append('핵심어 찾기 전략을 집중 연습하세요')
    
    if '주제 요약' in weaknesses:
        recommendations.append('요약 전략 학습을 강화하세요')
    
    streak = session_data.get('streak', 0)
    if streak < 3:
        recommendations.append('매일 꾸준히 학습하여 연속 학습을 유지하세요')
    
    return recommendations if recommendations else ['훌륭합니다! 현재 수준을 유지하세요']

if __name__ == '__main__':
    # Initialize database tables
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS responses (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255),
                task_id VARCHAR(255),
                question_type VARCHAR(50),
                answer TEXT,
                score FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_id ON responses(user_id);
            CREATE INDEX IF NOT EXISTS idx_task_id ON responses(task_id);
            CREATE INDEX IF NOT EXISTS idx_created_at ON responses(created_at);
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("Database initialized")
    except Exception as e:
        print(f"Database initialization error: {e}")
    
    # Run with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)