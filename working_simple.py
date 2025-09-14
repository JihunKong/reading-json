#!/usr/bin/env python3
"""
확실히 작동하는 간단한 한국어 독해 학습 웹 시스템
"""

from flask import Flask, render_template_string, request, jsonify
import json
import os
import random
import glob

app = Flask(__name__)

# 간단한 HTML 템플릿
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>한국어 독해 학습</title>
    <style>
        body { font-family: '맑은 고딕', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .container { background: white; padding: 20px; border-radius: 8px; }
        h1 { color: #2E7D32; text-align: center; }
        .reading-box { background: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 5px; line-height: 1.6; }
        .question-box { background: #e8f5e8; padding: 15px; margin: 15px 0; border-radius: 5px; }
        .choices { margin: 10px 0; }
        .choice { margin: 10px 0; padding: 10px; background: white; border: 1px solid #ddd; border-radius: 5px; cursor: pointer; }
        .choice:hover { background: #f0f8ff; }
        .choice.selected { background: #d4edda; border-color: #c3e6cb; }
        button { background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 10px 5px; }
        button:hover { background: #45a049; }
        button:disabled { background: #ccc; cursor: not-allowed; }
        .feedback { margin: 15px 0; padding: 15px; border-radius: 5px; }
        .feedback.correct { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .feedback.incorrect { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .hidden { display: none; }
        .progress { background: #e0e0e0; height: 20px; border-radius: 10px; margin: 20px 0; overflow: hidden; }
        .progress-bar { background: #4CAF50; height: 100%; width: 0%; transition: width 0.5s; }
        textarea { width: 100%; height: 100px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        .status { text-align: center; padding: 20px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 한국어 독해 학습</h1>
        
        <div class="progress">
            <div class="progress-bar" id="progress"></div>
        </div>
        
        <div id="status" class="status">
            <button onclick="startLearning()">학습 시작</button>
        </div>
        
        <div id="content" class="hidden">
            <div id="reading" class="reading-box"></div>
            
            <div id="question1" class="question-box hidden">
                <h3>[문제 1] 핵심어 선택</h3>
                <p id="q1-stem"></p>
                <div id="q1-choices" class="choices"></div>
                <button onclick="submitQ1()">답안 제출</button>
                <div id="q1-feedback" class="feedback hidden"></div>
            </div>
            
            <div id="question2" class="question-box hidden">
                <h3>[문제 2] 중심 문장</h3>
                <p id="q2-stem"></p>
                <div id="q2-choices" class="choices"></div>
                <button onclick="submitQ2()">답안 제출</button>
                <div id="q2-feedback" class="feedback hidden"></div>
            </div>
            
            <div id="question3" class="question-box hidden">
                <h3>[문제 3] 주제 파악</h3>
                <p id="q3-stem"></p>
                <textarea id="q3-answer" placeholder="이 문단의 주제를 한 문장으로 요약해주세요."></textarea>
                <button onclick="submitQ3()">답안 제출</button>
                <div id="q3-feedback" class="feedback hidden"></div>
            </div>
            
            <div id="complete" class="hidden">
                <div class="status">
                    <h3>🎉 학습 완료!</h3>
                    <button onclick="startLearning()">새 문제 풀기</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentTask = null;
        let currentQuestion = 0;
        let selectedAnswers = [null, null, null];
        
        function updateProgress() {
            const progress = (currentQuestion / 3) * 100;
            document.getElementById('progress').style.width = progress + '%';
        }
        
        function startLearning() {
            console.log('학습 시작...');
            document.getElementById('status').innerHTML = '<div class="status">📖 문제를 불러오고 있습니다...</div>';
            
            fetch('/get_task', {
                method: 'GET'
            })
            .then(response => {
                console.log('응답 상태:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('받은 데이터:', data);
                if (data.success) {
                    currentTask = data.task;
                    loadTask();
                } else {
                    alert('문제를 불러올 수 없습니다: ' + data.message);
                }
            })
            .catch(error => {
                console.error('오류:', error);
                alert('네트워크 오류가 발생했습니다.');
            });
        }
        
        function loadTask() {
            if (!currentTask) return;
            
            console.log('태스크 로드:', currentTask);
            
            // 읽기 자료 표시
            let content = '';
            if (currentTask.task_type === 'paragraph') {
                content = currentTask.paragraph.text;
            } else {
                content = currentTask.article.paragraphs.map(p => typeof p === 'string' ? p : p.text).join('<br><br>');
            }
            document.getElementById('reading').innerHTML = content;
            
            // 문제 1: 핵심어
            const q1 = currentTask.q_keywords_mcq;
            document.getElementById('q1-stem').textContent = q1.stem || '이 문단의 핵심 키워드는 무엇입니까?';
            document.getElementById('q1-choices').innerHTML = q1.choices.map((choice, i) => 
                `<div class="choice" onclick="selectChoice(1, ${i})" data-index="${i}">${i+1}. ${choice}</div>`
            ).join('');
            
            // 문제 2: 중심 문장
            const q2 = currentTask.q_center_sentence_mcq || currentTask.q_center_paragraph_mcq;
            document.getElementById('q2-stem').textContent = q2.stem || '이 문단의 중심 문장은 무엇입니까?';
            document.getElementById('q2-choices').innerHTML = q2.choices.map((choice, i) => 
                `<div class="choice" onclick="selectChoice(2, ${i})" data-index="${i}">${i+1}. ${choice}</div>`
            ).join('');
            
            // 문제 3: 주제
            const q3 = currentTask.q_topic_free;
            document.getElementById('q3-stem').textContent = q3.question || '이 문단의 주제를 한 문장으로 요약하세요.';
            
            // 초기화
            currentQuestion = 0;
            selectedAnswers = [null, null, null];
            ['q1-feedback', 'q2-feedback', 'q3-feedback'].forEach(id => {
                document.getElementById(id).className = 'feedback hidden';
            });
            
            // 화면 표시
            document.getElementById('status').className = 'hidden';
            document.getElementById('content').className = '';
            document.getElementById('complete').className = 'hidden';
            showQuestion(1);
        }
        
        function selectChoice(questionNum, choiceIndex) {
            const container = document.getElementById(`q${questionNum}-choices`);
            container.querySelectorAll('.choice').forEach(c => c.classList.remove('selected'));
            container.querySelector(`[data-index="${choiceIndex}"]`).classList.add('selected');
            selectedAnswers[questionNum - 1] = choiceIndex;
        }
        
        function showQuestion(qNum) {
            [1, 2, 3].forEach(i => {
                document.getElementById(`question${i}`).className = 'question-box hidden';
            });
            document.getElementById(`question${qNum}`).className = 'question-box';
            currentQuestion = qNum;
            updateProgress();
        }
        
        function submitQ1() {
            if (selectedAnswers[0] === null) {
                alert('답을 선택해주세요.');
                return;
            }
            
            fetch('/submit_answer', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    task_id: currentTask.id,
                    question_type: 'keywords',
                    answer: selectedAnswers[0]
                })
            })
            .then(response => response.json())
            .then(data => {
                showFeedback(1, data.correct, data.feedback);
                setTimeout(() => showQuestion(2), 2000);
            });
        }
        
        function submitQ2() {
            if (selectedAnswers[1] === null) {
                alert('답을 선택해주세요.');
                return;
            }
            
            fetch('/submit_answer', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    task_id: currentTask.id,
                    question_type: 'center',
                    answer: selectedAnswers[1]
                })
            })
            .then(response => response.json())
            .then(data => {
                showFeedback(2, data.correct, data.feedback);
                setTimeout(() => showQuestion(3), 2000);
            });
        }
        
        function submitQ3() {
            const answer = document.getElementById('q3-answer').value.trim();
            if (!answer) {
                alert('답을 작성해주세요.');
                return;
            }
            
            fetch('/submit_answer', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    task_id: currentTask.id,
                    question_type: 'topic',
                    answer: answer
                })
            })
            .then(response => response.json())
            .then(data => {
                showFeedback(3, data.correct, data.feedback);
                setTimeout(() => {
                    document.getElementById('question3').className = 'question-box hidden';
                    document.getElementById('complete').className = '';
                    updateProgress();
                }, 2000);
            });
        }
        
        function showFeedback(qNum, correct, message) {
            const feedback = document.getElementById(`q${qNum}-feedback`);
            feedback.textContent = message;
            feedback.className = `feedback ${correct ? 'correct' : 'incorrect'}`;
        }
        
        console.log('페이지 로드 완료');
    </script>
</body>
</html>
"""

class SimpleLearningSystem:
    def __init__(self):
        self.tasks = self.load_tasks()
        self.used_tasks = set()
    
    def load_tasks(self):
        tasks = []
        json_files = glob.glob("out/*.json")
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    task = json.load(f)
                    tasks.append(task)
            except Exception as e:
                print(f"Failed to load {file_path}: {e}")
        
        print(f"Loaded {len(tasks)} tasks")
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
    
    def calculate_similarity(self, text1, text2):
        import re
        from collections import Counter
        import math
        
        words1 = re.findall(r'[가-힣]+', text1.lower())
        words2 = re.findall(r'[가-힣]+', text2.lower())
        
        if not words1 or not words2:
            return 0.0
        
        counter1 = Counter(words1)
        counter2 = Counter(words2)
        
        all_words = set(counter1.keys()) | set(counter2.keys())
        
        dot_product = sum(counter1.get(word, 0) * counter2.get(word, 0) for word in all_words)
        magnitude1 = math.sqrt(sum(count ** 2 for count in counter1.values()))
        magnitude2 = math.sqrt(sum(count ** 2 for count in counter2.values()))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)

system = SimpleLearningSystem()

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/get_task')
def get_task():
    task = system.get_random_task()
    if task:
        print(f"Serving task: {task['id']}")
        return jsonify({'success': True, 'task': task})
    return jsonify({'success': False, 'message': 'No tasks available'})

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = request.json
    task_id = data['task_id']
    question_type = data['question_type']
    answer = data['answer']
    
    # Find task
    task = None
    for t in system.tasks:
        if t['id'] == task_id:
            task = t
            break
    
    if not task:
        return jsonify({'success': False, 'message': 'Task not found'})
    
    correct = False
    feedback = ""
    
    if question_type == 'keywords':
        q = task['q_keywords_mcq']
        correct = (answer == q['answer_index'])
        if correct:
            feedback = "정답입니다! 핵심어를 잘 파악했습니다."
        else:
            feedback = f"오답입니다. 정답은 {q['answer_index'] + 1}번 '{q['choices'][q['answer_index']]}'입니다."
    
    elif question_type == 'center':
        if task['task_type'] == 'paragraph':
            q = task['q_center_sentence_mcq']
        else:
            q = task['q_center_paragraph_mcq']
        
        answer_idx = q.get('answer_idx', q.get('answer_index', 0))
        correct = (answer == answer_idx)
        
        if correct:
            feedback = "정답입니다! 중심 내용을 잘 찾았습니다."
        else:
            feedback = f"오답입니다. 정답은 {answer_idx + 1}번 '{q['choices'][answer_idx]}'입니다."
    
    elif question_type == 'topic':
        q = task['q_topic_free']
        target = q.get('target_answer', q.get('target_topic', ''))
        
        similarity = system.calculate_similarity(answer, target)
        min_sim = 0.3  # 30% 유사도
        correct = similarity >= min_sim
        
        if correct:
            feedback = f"좋은 답변입니다! (유사도: {similarity:.1%})"
        else:
            feedback = f"더 구체적으로 작성해보세요. (유사도: {similarity:.1%})\n모범답안: {target}"
    
    return jsonify({
        'success': True,
        'correct': correct,
        'feedback': feedback
    })

if __name__ == '__main__':
    print(f"Simple Korean Reading System")
    print(f"Tasks loaded: {len(system.tasks)}")
    if system.tasks:
        print("Sample tasks:", [t['id'] for t in system.tasks[:3]])
    
    app.run(host='0.0.0.0', port=8080, debug=True)