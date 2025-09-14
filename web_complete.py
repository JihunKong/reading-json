#!/usr/bin/env python3
"""
Complete Korean Reading Comprehension Web Interface
All features fully implemented including WebSocket support
"""

from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import json
import os
import random
import glob
from datetime import datetime
import re
from typing import Dict, List, Optional

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-2025')
app.config['SESSION_TYPE'] = 'filesystem'

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

class CompleteLearningSystem:
    """Complete learning system with all features"""
    
    def __init__(self):
        self.task_dir = "out"
        self.tasks = self.load_tasks()
        self.user_highlights = {}  # Store highlights per user
        self.used_task_ids = set()  # Track used tasks
        self.summarization_strategies = {
            'micro': self.micro_summarization,
            'macro': self.macro_summarization,
            'gist': self.gist_method,
            'reciprocal': self.reciprocal_teaching
        }
        
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
        """Get a random task without repetition"""
        available_tasks = [t for t in self.tasks if t['id'] not in self.used_task_ids]
        if not available_tasks:
            # Reset if all tasks have been used
            self.used_task_ids.clear()
            available_tasks = self.tasks
        
        if available_tasks:
            task = random.choice(available_tasks)
            self.used_task_ids.add(task['id'])
            return task
        return None
    
    def get_adaptive_task(self, user_level: float):
        """Get task based on user level without repetition"""
        # Determine target difficulty
        if user_level < 0.4:
            target_difficulty = 'easy'
        elif user_level < 0.7:
            target_difficulty = 'medium'
        else:
            target_difficulty = 'hard'
        
        # Filter tasks by difficulty and exclude used ones
        filtered = [t for t in self.tasks 
                   if t.get('metainfo', {}).get('difficulty') == target_difficulty
                   and t['id'] not in self.used_task_ids]
        
        if not filtered:
            # Try all unused tasks regardless of difficulty
            filtered = [t for t in self.tasks if t['id'] not in self.used_task_ids]
        
        if not filtered:
            # Reset if all tasks have been used
            self.used_task_ids.clear()
            filtered = [t for t in self.tasks 
                       if t.get('metainfo', {}).get('difficulty') == target_difficulty]
            if not filtered:
                filtered = self.tasks
        
        if filtered:
            task = random.choice(filtered)
            self.used_task_ids.add(task['id'])
            return task
        return None
    
    def micro_summarization(self, text: str, max_words: int = 10) -> Dict:
        """Sentence-level summarization"""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        summaries = []
        
        for sentence in sentences:
            if sentence:
                words = sentence.split()
                if len(words) <= max_words:
                    summaries.append(sentence)
                else:
                    # Take key words
                    important = words[:max_words//2] + ['...'] + words[-max_words//2:]
                    summaries.append(' '.join(important))
        
        return {
            'strategy': 'micro',
            'summaries': summaries,
            'feedback': '각 문장의 핵심을 추출했습니다.',
            'count': len(summaries)
        }
    
    def macro_summarization(self, text: str) -> Dict:
        """Paragraph/article level summarization"""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        # Find key patterns
        main_idea = None
        for sentence in sentences:
            if any(keyword in sentence for keyword in ['중요한', '핵심', '결론', '요약']):
                main_idea = sentence
                break
        
        if not main_idea and sentences:
            # Take first and last sentences
            main_idea = f"{sentences[0]}. {sentences[-1] if len(sentences) > 1 else ''}"
        
        return {
            'strategy': 'macro',
            'summary': main_idea or "주요 내용을 찾을 수 없습니다.",
            'structure': {
                'introduction': sentences[0] if sentences else '',
                'body': sentences[1:-1] if len(sentences) > 2 else [],
                'conclusion': sentences[-1] if len(sentences) > 1 else ''
            },
            'feedback': '글의 전체 구조를 파악했습니다.'
        }
    
    def gist_method(self, text: str) -> Dict:
        """GIST method implementation"""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        segments = []
        
        # Break into segments (3 sentences each)
        for i in range(0, len(sentences), 3):
            segment_text = '. '.join(sentences[i:i+3])
            if segment_text:
                # Extract gist (first 7 words of segment)
                words = segment_text.split()[:7]
                gist = ' '.join(words) + ('...' if len(segment_text.split()) > 7 else '')
                segments.append({
                    'text': segment_text,
                    'gist': gist
                })
        
        # Combine all gists
        overall_gist = ' → '.join([s['gist'] for s in segments])
        
        return {
            'strategy': 'gist',
            'segments': segments,
            'overall_gist': overall_gist,
            'feedback': 'GIST 방법으로 핵심을 추출했습니다.'
        }
    
    def reciprocal_teaching(self, text: str) -> Dict:
        """Reciprocal teaching strategy"""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        # Generate components
        predictions = [
            "다음 단락에서는 구체적인 예시가 나올 것입니다",
            "이 개념의 실제 적용 사례가 설명될 것입니다"
        ]
        
        questions = [
            "이 글의 주요 논점은 무엇인가요?",
            "저자가 전달하고자 하는 핵심 메시지는?",
            "제시된 근거는 충분한가요?"
        ]
        
        # Identify difficult parts (long sentences)
        difficult = [s for s in sentences if len(s.split()) > 20][:2]
        if not difficult:
            difficult = ["명확하게 이해되는 내용입니다"]
        
        # Create summary
        summary = f"{sentences[0] if sentences else ''}. {sentences[-1] if len(sentences) > 1 else ''}"
        
        return {
            'strategy': 'reciprocal',
            'components': {
                'predicting': predictions,
                'questioning': questions,
                'clarifying': difficult,
                'summarizing': summary
            },
            'feedback': '상호교수법의 4가지 전략을 활용했습니다.'
        }
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between texts"""
        from collections import Counter
        import math
        
        # Extract Korean words and create frequency vectors
        words1 = re.findall(r'[가-힣]+', text1.lower())
        words2 = re.findall(r'[가-힣]+', text2.lower())
        
        if not words1 or not words2:
            return 0.0
        
        # Create frequency counters
        counter1 = Counter(words1)
        counter2 = Counter(words2)
        
        # Get all unique words
        all_words = set(counter1.keys()) | set(counter2.keys())
        
        # Calculate cosine similarity
        dot_product = sum(counter1.get(word, 0) * counter2.get(word, 0) for word in all_words)
        magnitude1 = math.sqrt(sum(count ** 2 for count in counter1.values()))
        magnitude2 = math.sqrt(sum(count ** 2 for count in counter2.values()))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        cosine_sim = dot_product / (magnitude1 * magnitude2)
        return cosine_sim

learning_system = CompleteLearningSystem()

# Session management
def init_session():
    """Initialize user session"""
    if 'user_id' not in session:
        session['user_id'] = os.urandom(16).hex()
        session['user_level'] = 0.5
        session['score_history'] = []
        session['total_tasks'] = 0
        session['correct_answers'] = 0
        session['streak'] = 0
        session['current_question'] = 0
        session['current_task_id'] = None
        session['highlights'] = []
        session['last_activity'] = datetime.now().isoformat()

def update_user_level(score: float):
    """Update user level based on performance"""
    if 'user_level' not in session:
        session['user_level'] = 0.5
    
    current_level = session['user_level']
    
    # Adaptive learning rate
    learning_rate = 0.1
    performance_delta = score - 0.7  # Target is 70% accuracy
    level_change = learning_rate * performance_delta
    
    new_level = current_level + level_change
    session['user_level'] = max(0.1, min(1.0, new_level))

# Routes
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
    init_session()
    return render_template('simple_study.html')

@app.route('/api/get_task', methods=['POST'])
def get_task():
    """Get adaptive task with summarization support"""
    init_session()
    
    data = request.json
    strategy = data.get('strategy', 'adaptive')
    
    # Get task based on strategy
    if strategy == 'adaptive':
        user_level = session.get('user_level', 0.5)
        task = learning_system.get_adaptive_task(user_level)
    else:
        task = learning_system.get_random_task()
    
    if task:
        # Store task info in session
        session['current_task_id'] = task['id']
        session['current_question'] = 0
        session['task_start_time'] = datetime.now().isoformat()
        
        # Apply summarization strategy if requested
        summary_strategy = data.get('summarization_strategy', 'micro')
        if summary_strategy in learning_system.summarization_strategies:
            # Extract text based on task type
            if task['task_type'] == 'paragraph':
                text = task.get('paragraph', {}).get('text', '')
            else:
                paragraphs = task.get('article', {}).get('paragraphs', [])
                if paragraphs and isinstance(paragraphs[0], dict):
                    text = ' '.join([p.get('text', '') for p in paragraphs])
                else:
                    text = ' '.join(paragraphs)
            
            # Apply strategy
            summary_data = learning_system.summarization_strategies[summary_strategy](text)
            task['summary_assistance'] = summary_data
        
        # Calculate reading complexity
        if task['task_type'] == 'paragraph':
            text = task.get('paragraph', {}).get('text', '')
        else:
            paragraphs = task.get('article', {}).get('paragraphs', [])
            if paragraphs and isinstance(paragraphs[0], dict):
                text = ' '.join([p.get('text', '') for p in paragraphs])
            else:
                text = ' '.join(paragraphs)
        
        sentences = text.split('.')
        words = text.split()
        
        if sentences and words:
            avg_sentence_length = len(words) / len(sentences)
            complexity = min(max(avg_sentence_length / 50, 0.1), 1.0)
            task['complexity_level'] = complexity
        
        return jsonify({'success': True, 'task': task})
    
    return jsonify({'success': False, 'message': 'No tasks available'})

@app.route('/api/submit_answer', methods=['POST'])
def submit_answer():
    """Submit and evaluate answer with progress tracking"""
    init_session()
    
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
    
    # Evaluate answer
    correct = False
    feedback = ""
    score = 0
    
    if question_type == 'keywords':
        q = current_task['q_keywords_mcq']
        correct = answer == q['answer_index']
        if correct:
            feedback = "정답입니다! 핵심어를 잘 파악했습니다."
        else:
            feedback = f"오답입니다. 정답은 {q['answer_index'] + 1}번입니다.\n"
            feedback += f"정답: {q['choices'][q['answer_index']]}\n"
            if 'rationale' in q:
                feedback += f"설명: {q['rationale']}"
        score = 1.0 if correct else 0.0
        
    elif question_type == 'center':
        if current_task['task_type'] == 'paragraph':
            q = current_task['q_center_sentence_mcq']
            answer_idx = q.get('answer_idx', q.get('answer_index'))
            correct = (answer == answer_idx)
            if correct:
                feedback = "정답입니다! 중심 내용을 잘 찾았습니다."
            else:
                feedback = f"오답입니다. 정답은 {answer_idx + 1}번입니다.\n"
                if 'choices' in q:
                    feedback += f"정답: {q['choices'][answer_idx]}\n"
                if 'rationale' in q:
                    feedback += f"설명: {q['rationale']}"
        else:
            q = current_task['q_center_paragraph_mcq']
            answer_idx = q.get('answer_idx', q.get('answer_index'))
            correct = (answer == answer_idx)
            if correct:
                feedback = "정답입니다! 중심 내용을 잘 찾았습니다."
            else:
                feedback = f"오답입니다. 정답은 {answer_idx + 1}번입니다.\n"
                if 'choices' in q:
                    feedback += f"정답: {q['choices'][answer_idx]['text']}\n"
                if 'rationale' in q:
                    feedback += f"설명: {q['rationale']}"
        score = 1.0 if correct else 0.0
        
    elif question_type == 'topic':
        q = current_task.get('q_topic_free', {})
        target = q.get('target_answer', q.get('target_topic', '주제를 명확하게 표현해주세요.'))
        
        # Calculate similarity
        similarity = learning_system.calculate_similarity(answer, target)
        score = similarity
        # Lower threshold for cosine similarity (more lenient)
        eval_criteria = q.get('evaluation_criteria', q.get('evaluation', {}))
        min_sim = eval_criteria.get('min_similarity', 0.5) * 0.4  # Lower threshold to ~20-30%
        correct = similarity >= min_sim
        
        if correct:
            feedback = f"좋은 답변입니다! (코사인 유사도: {similarity:.2%})"
        else:
            feedback = f"더 구체적으로 작성해보세요. (코사인 유사도: {similarity:.2%})\n"
            feedback += f"모범답안: {target}\n"
            feedback += f"필요 유사도: {min_sim:.2%} 이상\n"
            if 'feedback_guides' in q:
                feedback += "힌트:\n" + "\n".join([f"• {guide}" for guide in q['feedback_guides']])
    
    # Update session statistics
    session['total_tasks'] = session.get('total_tasks', 0) + 1
    if correct:
        session['correct_answers'] = session.get('correct_answers', 0) + 1
    
    # Update user level
    update_user_level(score)
    
    # Track score history
    if 'score_history' not in session:
        session['score_history'] = []
    
    session['score_history'].append({
        'task_id': task_id,
        'question_type': question_type,
        'score': score,
        'timestamp': datetime.now().isoformat()
    })
    
    # Update current question index
    session['current_question'] = session.get('current_question', 0) + 1
    
    # Check if task is complete (all 3 questions answered)
    task_complete = session['current_question'] >= 3
    
    return jsonify({
        'success': True,
        'correct': correct,
        'feedback': feedback,
        'score': score,
        'user_level': session.get('user_level', 0.5),
        'streak': session.get('streak', 0),
        'current_question': session['current_question'],
        'task_complete': task_complete
    })

@app.route('/api/get_progress')
def get_progress():
    """Get detailed user progress"""
    init_session()
    
    total_tasks = session.get('total_tasks', 0)
    correct_answers = session.get('correct_answers', 0)
    
    accuracy = (correct_answers / total_tasks * 100) if total_tasks > 0 else 0
    
    # Calculate achievements
    achievements = []
    if total_tasks >= 10:
        achievements.append({'name': '첫 걸음', 'icon': '🌱', 'description': '10개 과제 완료'})
    if total_tasks >= 50:
        achievements.append({'name': '꾸준한 학습자', 'icon': '🌿', 'description': '50개 과제 완료'})
    if accuracy >= 80 and total_tasks >= 10:
        achievements.append({'name': '우수 학습자', 'icon': '⭐', 'description': '80% 이상 정답률'})
    
    return jsonify({
        'success': True,
        'progress': {
            'user_level': session.get('user_level', 0.5),
            'total_tasks': total_tasks,
            'correct_answers': correct_answers,
            'accuracy': accuracy,
            'streak': session.get('streak', 0),
            'score_history': session.get('score_history', [])[-10:],  # Last 10
            'achievements': achievements,
            'current_question': session.get('current_question', 0)
        }
    })

@app.route('/api/save_highlight', methods=['POST'])
def save_highlight():
    """Save text highlight"""
    init_session()
    
    data = request.json
    highlight = {
        'task_id': data.get('task_id'),
        'text': data.get('text'),
        'category': data.get('category'),
        'timestamp': datetime.now().isoformat()
    }
    
    if 'highlights' not in session:
        session['highlights'] = []
    
    session['highlights'].append(highlight)
    
    # Store in system for this user
    user_id = session['user_id']
    if user_id not in learning_system.user_highlights:
        learning_system.user_highlights[user_id] = []
    
    learning_system.user_highlights[user_id].append(highlight)
    
    return jsonify({'success': True, 'highlight': highlight})

@app.route('/api/get_highlights')
def get_highlights():
    """Get user's highlights"""
    init_session()
    
    user_id = session['user_id']
    highlights = learning_system.user_highlights.get(user_id, [])
    
    return jsonify({
        'success': True,
        'highlights': highlights
    })

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    init_session()
    emit('connected', {
        'message': '학습 시스템에 연결되었습니다',
        'user_id': session.get('user_id')
    })
    print(f"Client connected: {session.get('user_id')}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected: {session.get('user_id', 'unknown')}")

@socketio.on('start_reading')
def handle_start_reading(data):
    """Track reading start"""
    task_id = data.get('task_id')
    emit('reading_started', {
        'task_id': task_id,
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('highlight_text')
def handle_highlight(data):
    """Handle text highlighting with real-time sharing"""
    init_session()
    
    highlight = {
        'task_id': data.get('task_id'),
        'text': data.get('text'),
        'category': data.get('category'),
        'user': session.get('user_id'),
        'timestamp': datetime.now().isoformat()
    }
    
    # Save to user's highlights
    if 'highlights' not in session:
        session['highlights'] = []
    session['highlights'].append(highlight)
    
    # Broadcast to all users (optional - for collaborative learning)
    emit('text_highlighted', highlight, broadcast=True)

@socketio.on('request_help')
def handle_help_request(data):
    """Handle help request"""
    question_type = data.get('question_type')
    
    help_messages = {
        'keywords': '핵심어는 글 전체에서 가장 중요한 개념을 나타내는 단어입니다.',
        'center': '중심 문장/문단은 글의 주제를 가장 잘 나타내는 부분입니다.',
        'topic': '주제는 글 전체가 전달하고자 하는 핵심 메시지입니다.'
    }
    
    emit('help_provided', {
        'message': help_messages.get(question_type, '도움말을 제공할 수 없습니다.')
    })

if __name__ == '__main__':
    print(f"Starting Complete Korean Reading Comprehension System")
    print(f"Tasks loaded: {len(learning_system.tasks)}")
    if learning_system.tasks:
        print("Sample task IDs:", [t['id'] for t in learning_system.tasks[:3]])
    
    # Run with SocketIO (allow_unsafe_werkzeug for development)
    socketio.run(app, host='0.0.0.0', port=8080, debug=True, allow_unsafe_werkzeug=True)