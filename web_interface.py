#!/usr/bin/env python3
"""
웹 기반 한국어 읽기 이해 학습 인터페이스
Flask를 사용한 대화형 웹 애플리케이션
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
import random
import glob
from datetime import datetime
import secrets
from typing import Dict, List
import re

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# 전역 데이터 저장소
TASKS_DIR = "generator/out"
SESSIONS_DIR = "study_sessions"

# 세션 디렉토리 생성
os.makedirs(SESSIONS_DIR, exist_ok=True)

def load_all_tasks():
    """모든 과제 파일 로드"""
    tasks = []
    json_files = glob.glob(os.path.join(TASKS_DIR, "*.json"))
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                task = json.load(f)
                task['file_name'] = os.path.basename(file_path)
                tasks.append(task)
        except Exception as e:
            print(f"파일 로드 실패 {file_path}: {e}")
    
    return tasks

# 과제 데이터 로드
TASKS = load_all_tasks()

@app.route('/')
def index():
    """메인 페이지"""
    # 세션 초기화
    if 'user_id' not in session:
        session['user_id'] = secrets.token_hex(8)
        session['scores'] = []
        session['current_task_idx'] = 0
    
    stats = {
        'total_tasks': len(TASKS),
        'paragraph_count': len([t for t in TASKS if t['task_type'] == 'paragraph']),
        'article_count': len([t for t in TASKS if t['task_type'] == 'article']),
        'difficulties': {
            'easy': len([t for t in TASKS if t['metainfo']['difficulty'] == 'easy']),
            'medium': len([t for t in TASKS if t['metainfo']['difficulty'] == 'medium']),
            'hard': len([t for t in TASKS if t['metainfo']['difficulty'] == 'hard'])
        }
    }
    
    return '''
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>한국어 읽기 이해 학습 시스템</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Noto Sans KR', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .container {
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 800px;
                width: 90%;
            }
            h1 {
                color: #333;
                text-align: center;
                margin-bottom: 30px;
                font-size: 2.5em;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            .stat-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 15px;
                text-align: center;
            }
            .stat-number {
                font-size: 2em;
                font-weight: bold;
            }
            .stat-label {
                margin-top: 5px;
                opacity: 0.9;
            }
            .menu {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-top: 40px;
            }
            .menu-btn {
                background: white;
                border: 2px solid #667eea;
                color: #667eea;
                padding: 20px;
                border-radius: 15px;
                font-size: 1.1em;
                cursor: pointer;
                transition: all 0.3s;
                text-decoration: none;
                display: block;
                text-align: center;
            }
            .menu-btn:hover {
                background: #667eea;
                color: white;
                transform: translateY(-3px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }
            .emoji {
                font-size: 2em;
                display: block;
                margin-bottom: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📚 한국어 읽기 이해 학습 시스템</h1>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">''' + str(stats['total_tasks']) + '''</div>
                    <div class="stat-label">전체 과제</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">''' + str(stats['paragraph_count']) + '''</div>
                    <div class="stat-label">문단 과제</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">''' + str(stats['article_count']) + '''</div>
                    <div class="stat-label">글 과제</div>
                </div>
            </div>
            
            <div class="menu">
                <a href="/study/paragraph" class="menu-btn">
                    <span class="emoji">📝</span>
                    문단 읽기 연습
                </a>
                <a href="/study/article" class="menu-btn">
                    <span class="emoji">📖</span>
                    글 읽기 연습
                </a>
                <a href="/study/random" class="menu-btn">
                    <span class="emoji">🎲</span>
                    랜덤 학습
                </a>
                <a href="/progress" class="menu-btn">
                    <span class="emoji">📊</span>
                    학습 통계
                </a>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/study/<task_type>')
def study(task_type):
    """학습 페이지"""
    # 과제 선택
    if task_type == 'random':
        task = random.choice(TASKS) if TASKS else None
    elif task_type in ['paragraph', 'article']:
        filtered = [t for t in TASKS if t['task_type'] == task_type]
        task = random.choice(filtered) if filtered else None
    else:
        return redirect(url_for('index'))
    
    if not task:
        return "과제를 찾을 수 없습니다.", 404
    
    # 세션에 현재 과제 저장
    session['current_task'] = task
    
    # HTML 생성
    html_content = '''
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>읽기 학습</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Noto Sans KR', sans-serif;
                background: #f5f5f5;
                padding: 20px;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            }
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 2px solid #eee;
            }
            .back-btn {
                background: #667eea;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
            }
            .task-type {
                background: #764ba2;
                color: white;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.9em;
            }
            .content-area {
                margin: 30px 0;
                padding: 25px;
                background: #f9f9f9;
                border-radius: 10px;
                line-height: 1.8;
                font-size: 1.1em;
            }
            .topic-hint {
                color: #667eea;
                font-weight: bold;
                margin-bottom: 15px;
            }
            .paragraph-text, .article-paragraph {
                text-align: justify;
                margin-bottom: 20px;
            }
            .article-title {
                font-size: 1.4em;
                font-weight: bold;
                margin-bottom: 20px;
                color: #333;
            }
            .question-area {
                margin-top: 40px;
                padding: 25px;
                background: #fff;
                border: 2px solid #667eea;
                border-radius: 10px;
            }
            .question {
                font-size: 1.2em;
                font-weight: bold;
                margin-bottom: 20px;
                color: #333;
            }
            .choices {
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            .choice-btn {
                background: white;
                border: 2px solid #ddd;
                padding: 15px 20px;
                border-radius: 8px;
                cursor: pointer;
                text-align: left;
                transition: all 0.3s;
            }
            .choice-btn:hover {
                background: #f0f0f0;
                border-color: #667eea;
            }
            .choice-btn.selected {
                background: #667eea;
                color: white;
                border-color: #667eea;
            }
            .choice-btn.correct {
                background: #4caf50;
                color: white;
                border-color: #4caf50;
            }
            .choice-btn.incorrect {
                background: #f44336;
                color: white;
                border-color: #f44336;
            }
            .submit-btn {
                background: #667eea;
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 1.1em;
                cursor: pointer;
                margin-top: 20px;
            }
            .submit-btn:hover {
                background: #5a67d8;
            }
            .feedback {
                margin-top: 20px;
                padding: 15px;
                border-radius: 8px;
                display: none;
            }
            .feedback.correct {
                background: #e8f5e9;
                color: #2e7d32;
            }
            .feedback.incorrect {
                background: #ffebee;
                color: #c62828;
            }
            .next-btn {
                background: #4caf50;
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 1.1em;
                cursor: pointer;
                margin-top: 20px;
                display: none;
            }
            #freeResponseArea {
                margin-top: 20px;
            }
            #freeResponse {
                width: 100%;
                min-height: 100px;
                padding: 15px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 1em;
                resize: vertical;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <a href="/" class="back-btn">← 메인으로</a>
                <span class="task-type">''' + ('문단 과제' if task['task_type'] == 'paragraph' else '글 과제') + '''</span>
            </div>
            
            <div class="content-area">
    '''
    
    if task['task_type'] == 'paragraph':
        html_content += f'''
                <div class="topic-hint">주제: {task['paragraph']['topic_hint']}</div>
                <div class="paragraph-text">{task['paragraph']['text']}</div>
        '''
    else:
        html_content += f'''
                <div class="article-title">{task['article']['title']}</div>
        '''
        for idx, para in enumerate(task['article']['paragraphs'], 1):
            html_content += f'''
                <div class="article-paragraph">
                    <strong>[문단 {idx}]</strong><br>
                    {para}
                </div>
            '''
    
    html_content += '''
            </div>
            
            <div id="questionArea"></div>
            
        </div>
        
        <script>
            let currentQuestion = 0;
            let score = 0;
            let answers = [];
            const taskData = ''' + json.dumps(task) + ''';
            
            function showQuestion(qIndex) {
                const questionArea = document.getElementById('questionArea');
                let html = '<div class="question-area">';
                
                if (qIndex === 0) {
                    // 핵심어 문제
                    const q = taskData.q_keywords_mcq;
                    html += '<div class="question">[문제 1] ' + q.stem + '</div>';
                    html += '<div class="choices">';
                    q.choices.forEach((choice, idx) => {
                        html += `<button class="choice-btn" onclick="selectChoice(this, ${idx})">${idx+1}. ${choice}</button>`;
                    });
                    html += '</div>';
                    html += '<button class="submit-btn" onclick="checkAnswer(0)">답변 제출</button>';
                    
                } else if (qIndex === 1) {
                    // 중심문장/문단 문제
                    const q = taskData.task_type === 'paragraph' ? 
                        taskData.q_center_sentence_mcq : taskData.q_center_paragraph_mcq;
                    html += '<div class="question">[문제 2] ' + q.stem + '</div>';
                    html += '<div class="choices">';
                    
                    const items = q.sentences || q.choices;
                    items.forEach((item, idx) => {
                        html += `<button class="choice-btn" onclick="selectChoice(this, ${item.idx})">${item.idx}. ${item.text}</button>`;
                    });
                    html += '</div>';
                    html += '<button class="submit-btn" onclick="checkAnswer(1)">답변 제출</button>';
                    
                } else if (qIndex === 2) {
                    // 주제 서술형 문제
                    const q = taskData.q_topic_free;
                    html += '<div class="question">[문제 3] ' + q.stem + '</div>';
                    html += '<div id="freeResponseArea">';
                    html += '<textarea id="freeResponse" placeholder="답을 입력하세요..."></textarea>';
                    html += '</div>';
                    html += '<button class="submit-btn" onclick="checkFreeAnswer()">답변 제출</button>';
                }
                
                html += '<div id="feedback" class="feedback"></div>';
                html += '<button id="nextBtn" class="next-btn" onclick="nextQuestion()" style="display:none;">다음 문제 →</button>';
                html += '</div>';
                
                questionArea.innerHTML = html;
            }
            
            function selectChoice(btn, value) {
                const buttons = btn.parentElement.querySelectorAll('.choice-btn');
                buttons.forEach(b => b.classList.remove('selected'));
                btn.classList.add('selected');
                answers[currentQuestion] = value;
            }
            
            function checkAnswer(qIndex) {
                let correct = false;
                let feedback = '';
                
                if (qIndex === 0) {
                    const q = taskData.q_keywords_mcq;
                    correct = answers[qIndex] === q.answer_index;
                    feedback = correct ? '✅ 정답입니다!' : `❌ 틀렸습니다. 정답은 ${q.answer_index + 1}번입니다.<br>${q.rationale}`;
                    
                } else if (qIndex === 1) {
                    const q = taskData.task_type === 'paragraph' ? 
                        taskData.q_center_sentence_mcq : taskData.q_center_paragraph_mcq;
                    correct = answers[qIndex] === q.answer_idx;
                    feedback = correct ? '✅ 정답입니다!' : `❌ 틀렸습니다. 정답은 ${q.answer_idx}번입니다.<br>${q.rationale}`;
                }
                
                if (correct) score++;
                
                const feedbackDiv = document.getElementById('feedback');
                feedbackDiv.innerHTML = feedback;
                feedbackDiv.className = 'feedback ' + (correct ? 'correct' : 'incorrect');
                feedbackDiv.style.display = 'block';
                
                document.getElementById('nextBtn').style.display = 'block';
                document.querySelector('.submit-btn').style.display = 'none';
            }
            
            function checkFreeAnswer() {
                const answer = document.getElementById('freeResponse').value;
                const q = taskData.q_topic_free;
                
                // 간단한 키워드 매칭 (실제로는 서버에서 처리)
                const keywords = q.target_topic.match(/[가-힣]+/g) || [];
                const userKeywords = answer.match(/[가-힣]+/g) || [];
                const matches = keywords.filter(k => userKeywords.includes(k));
                const similarity = matches.length / Math.max(keywords.length, 1);
                
                let feedback = `<strong>모범답안:</strong> ${q.target_topic}<br><br>`;
                
                if (similarity >= 0.5) {
                    feedback += '✅ 좋은 답변입니다!';
                    score++;
                } else {
                    feedback += '⚠️ 더 구체적으로 작성해보세요.<br>';
                    q.feedback_guides.forEach(guide => {
                        feedback += `• ${guide}<br>`;
                    });
                }
                
                const feedbackDiv = document.getElementById('feedback');
                feedbackDiv.innerHTML = feedback;
                feedbackDiv.className = 'feedback ' + (similarity >= 0.5 ? 'correct' : 'incorrect');
                feedbackDiv.style.display = 'block';
                
                document.getElementById('nextBtn').style.display = 'block';
                document.getElementById('nextBtn').innerText = '결과 보기';
                document.querySelector('.submit-btn').style.display = 'none';
            }
            
            function nextQuestion() {
                currentQuestion++;
                
                if (currentQuestion < 3) {
                    showQuestion(currentQuestion);
                } else {
                    // 최종 결과 표시
                    showResults();
                }
            }
            
            function showResults() {
                const percentage = Math.round(score / 3 * 100);
                let message = '';
                
                if (score === 3) {
                    message = '🎉 완벽합니다! 모든 문제를 맞췄습니다!';
                } else if (score >= 2) {
                    message = '👍 잘했습니다! 계속 연습하세요.';
                } else {
                    message = '💪 더 연습이 필요합니다. 다시 도전해보세요!';
                }
                
                const questionArea = document.getElementById('questionArea');
                questionArea.innerHTML = `
                    <div class="question-area" style="text-align: center;">
                        <h2 style="color: #667eea; margin-bottom: 20px;">학습 완료!</h2>
                        <div style="font-size: 3em; margin: 20px 0;">${score}/3</div>
                        <div style="font-size: 1.5em; margin-bottom: 20px;">${percentage}%</div>
                        <div style="font-size: 1.2em; margin-bottom: 30px;">${message}</div>
                        <a href="/" class="submit-btn" style="text-decoration: none; display: inline-block;">메인으로</a>
                        <a href="/study/${taskData.task_type}" class="next-btn" style="text-decoration: none; display: inline-block; margin-left: 10px;">다시 도전</a>
                    </div>
                `;
                
                // 서버에 결과 저장
                saveResults();
            }
            
            function saveResults() {
                fetch('/save_result', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        task_id: taskData.id,
                        task_type: taskData.task_type,
                        difficulty: taskData.metainfo.difficulty,
                        score: score,
                        total: 3
                    })
                });
            }
            
            // 첫 문제 표시
            showQuestion(0);
        </script>
    </body>
    </html>
    '''
    
    return html_content

@app.route('/save_result', methods=['POST'])
def save_result():
    """학습 결과 저장"""
    data = request.json
    
    if 'scores' not in session:
        session['scores'] = []
    
    result = {
        **data,
        'timestamp': datetime.now().isoformat(),
        'user_id': session.get('user_id')
    }
    
    session['scores'].append(result)
    
    # 파일로도 저장
    user_file = os.path.join(SESSIONS_DIR, f"{session['user_id']}.json")
    
    try:
        if os.path.exists(user_file):
            with open(user_file, 'r', encoding='utf-8') as f:
                all_scores = json.load(f)
        else:
            all_scores = []
        
        all_scores.append(result)
        
        with open(user_file, 'w', encoding='utf-8') as f:
            json.dump(all_scores, f, ensure_ascii=False, indent=2)
    except:
        pass
    
    return jsonify({'status': 'success'})

@app.route('/progress')
def progress():
    """학습 통계 페이지"""
    user_file = os.path.join(SESSIONS_DIR, f"{session.get('user_id', 'unknown')}.json")
    
    scores = []
    if os.path.exists(user_file):
        with open(user_file, 'r', encoding='utf-8') as f:
            scores = json.load(f)
    
    # 통계 계산
    total_tasks = len(scores)
    avg_score = sum(s['score'] for s in scores) / total_tasks if total_tasks > 0 else 0
    
    # 난이도별 통계
    stats_by_difficulty = {}
    for diff in ['easy', 'medium', 'hard']:
        diff_scores = [s for s in scores if s['difficulty'] == diff]
        if diff_scores:
            stats_by_difficulty[diff] = {
                'count': len(diff_scores),
                'avg': sum(s['score'] for s in diff_scores) / len(diff_scores)
            }
    
    # 타입별 통계
    para_scores = [s for s in scores if s['task_type'] == 'paragraph']
    art_scores = [s for s in scores if s['task_type'] == 'article']
    
    html = '''
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>학습 통계</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Noto Sans KR', sans-serif;
                background: #f5f5f5;
                padding: 20px;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            }
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 30px;
            }
            .back-btn {
                background: #667eea;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                text-decoration: none;
                display: inline-block;
            }
            h1 { color: #333; }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            .stat-box {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 25px;
                border-radius: 15px;
                text-align: center;
            }
            .stat-value {
                font-size: 2.5em;
                font-weight: bold;
                margin-bottom: 10px;
            }
            .stat-label {
                opacity: 0.9;
            }
            .chart-container {
                margin: 30px 0;
                padding: 20px;
                background: #f9f9f9;
                border-radius: 10px;
            }
            .progress-bar {
                width: 100%;
                height: 30px;
                background: #e0e0e0;
                border-radius: 15px;
                overflow: hidden;
                margin: 10px 0;
            }
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #667eea, #764ba2);
                transition: width 0.5s;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 학습 통계</h1>
                <a href="/" class="back-btn">← 메인으로</a>
            </div>
            
            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-value">''' + str(total_tasks) + '''</div>
                    <div class="stat-label">총 학습 과제</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">''' + f"{avg_score:.1f}" + '''/3</div>
                    <div class="stat-label">평균 점수</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">''' + f"{avg_score/3*100:.0f}" + '''%</div>
                    <div class="stat-label">정답률</div>
                </div>
            </div>
    '''
    
    if stats_by_difficulty:
        html += '''
            <div class="chart-container">
                <h3>난이도별 성과</h3>
        '''
        for diff, stat in stats_by_difficulty.items():
            percentage = stat['avg'] / 3 * 100
            html += f'''
                <div style="margin: 15px 0;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>{diff.upper()}</span>
                        <span>{stat['count']}개 완료 (평균 {stat['avg']:.1f}/3)</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {percentage}%"></div>
                    </div>
                </div>
            '''
        html += '</div>'
    
    if para_scores or art_scores:
        html += '''
            <div class="chart-container">
                <h3>과제 유형별 성과</h3>
        '''
        if para_scores:
            para_avg = sum(s['score'] for s in para_scores) / len(para_scores)
            para_percentage = para_avg / 3 * 100
            html += f'''
                <div style="margin: 15px 0;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>문단 과제</span>
                        <span>{len(para_scores)}개 완료 (평균 {para_avg:.1f}/3)</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {para_percentage}%"></div>
                    </div>
                </div>
            '''
        
        if art_scores:
            art_avg = sum(s['score'] for s in art_scores) / len(art_scores)
            art_percentage = art_avg / 3 * 100
            html += f'''
                <div style="margin: 15px 0;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>글 과제</span>
                        <span>{len(art_scores)}개 완료 (평균 {art_avg:.1f}/3)</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {art_percentage}%"></div>
                    </div>
                </div>
            '''
        html += '</div>'
    
    html += '''
        </div>
    </body>
    </html>
    '''
    
    return html

if __name__ == '__main__':
    print("🚀 웹 서버 시작 중...")
    print("브라우저에서 http://localhost:5000 접속")
    app.run(debug=True, port=5000)