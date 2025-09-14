#!/usr/bin/env python3
"""
개선된 한국어 독해 학습 시스템
- 시간 제한 기능
- 상세한 해설
- 수동 진행 기능
- 핵심어 1개만 선택
"""

from flask import Flask, render_template_string, request, jsonify
import json
import os
import random
import glob
import re
from collections import Counter
import math

app = Flask(__name__)

# 개선된 HTML 템플릿
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>한국어 독해 학습 - 개선판</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: '맑은 고딕', 'Malgun Gothic', sans-serif; 
            max-width: 900px; 
            margin: 0 auto; 
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container { 
            background: white; 
            padding: 30px; 
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        
        h1 { 
            color: #5a67d8; 
            text-align: center;
            margin-bottom: 10px;
            font-size: 2em;
        }
        
        .subtitle {
            text-align: center;
            color: #718096;
            margin-bottom: 20px;
        }
        
        /* 타이머 스타일 */
        .timer-container {
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            display: none;
            z-index: 1000;
        }
        
        .timer {
            font-size: 24px;
            font-weight: bold;
            color: #2d3748;
        }
        
        .timer.warning {
            color: #f6ad55;
            animation: pulse 1s infinite;
        }
        
        .timer.danger {
            color: #fc8181;
            animation: pulse 0.5s infinite;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        .timer-bar {
            width: 100%;
            height: 6px;
            background: #e2e8f0;
            border-radius: 3px;
            margin-top: 10px;
            overflow: hidden;
        }
        
        .timer-fill {
            height: 100%;
            background: linear-gradient(90deg, #48bb78 0%, #38a169 100%);
            transition: width 1s linear;
        }
        
        /* 진행 바 */
        .progress {
            background: #e2e8f0;
            height: 8px;
            border-radius: 4px;
            margin: 20px 0;
            overflow: hidden;
        }
        
        .progress-bar {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            height: 100%;
            width: 0%;
            transition: width 0.5s ease;
        }
        
        /* 읽기 자료 */
        .reading-box {
            background: #f7fafc;
            padding: 25px;
            margin: 20px 0;
            border-radius: 10px;
            line-height: 1.8;
            font-size: 16px;
            border-left: 4px solid #667eea;
        }
        
        /* 문제 박스 */
        .question-box {
            background: linear-gradient(135deg, #f6f8fb 0%, #e9ecef 100%);
            padding: 20px;
            margin: 20px 0;
            border-radius: 10px;
            border: 1px solid #cbd5e0;
        }
        
        .question-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .question-number {
            background: #667eea;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
        }
        
        .time-limit {
            color: #718096;
            font-size: 14px;
        }
        
        /* 선택지 */
        .choices { margin: 15px 0; }
        
        .choice {
            margin: 10px 0;
            padding: 15px;
            background: white;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .choice:hover {
            background: #edf2f7;
            border-color: #667eea;
            transform: translateX(5px);
        }
        
        .choice.selected {
            background: #e9d8fd;
            border-color: #805ad5;
        }
        
        .choice.correct {
            background: #c6f6d5;
            border-color: #48bb78;
        }
        
        .choice.incorrect {
            background: #fed7d7;
            border-color: #fc8181;
        }
        
        /* 해설 박스 */
        .explanation {
            background: #f7fafc;
            border: 1px solid #cbd5e0;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            display: none;
        }
        
        .explanation-header {
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 10px;
            font-size: 18px;
        }
        
        .explanation-content {
            line-height: 1.6;
            color: #4a5568;
        }
        
        .explanation.show {
            display: block;
            animation: slideIn 0.5s ease;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .explanation-section {
            margin: 15px 0;
            padding: 10px;
            background: white;
            border-radius: 5px;
        }
        
        .explanation-label {
            font-weight: bold;
            color: #5a67d8;
            margin-bottom: 5px;
        }
        
        /* 버튼 */
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.3s ease;
            margin: 10px 5px;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        button:disabled {
            background: #cbd5e0;
            cursor: not-allowed;
            transform: none;
        }
        
        .button-container {
            text-align: center;
            margin: 20px 0;
        }
        
        .next-button {
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            display: none;
        }
        
        .next-button.show {
            display: inline-block;
        }
        
        /* 텍스트 입력 */
        textarea {
            width: 100%;
            height: 120px;
            padding: 12px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-family: inherit;
            font-size: 15px;
            resize: vertical;
            transition: border-color 0.3s ease;
        }
        
        textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        /* 상태 메시지 */
        .status {
            text-align: center;
            padding: 30px;
            color: #4a5568;
        }
        
        .hidden { display: none !important; }
        
        /* 통계 */
        .stats {
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
            padding: 15px;
            background: #f7fafc;
            border-radius: 10px;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-label {
            color: #718096;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 한국어 독해 학습 시스템</h1>
        <p class="subtitle">시간 제한과 상세 해설이 포함된 개선판</p>
        
        <!-- 타이머 -->
        <div class="timer-container" id="timerContainer">
            <div class="timer" id="timer">60</div>
            <div class="timer-bar">
                <div class="timer-fill" id="timerFill"></div>
            </div>
        </div>
        
        <!-- 진행 바 -->
        <div class="progress">
            <div class="progress-bar" id="progress"></div>
        </div>
        
        <!-- 통계 -->
        <div class="stats hidden" id="stats">
            <div class="stat-item">
                <div class="stat-value" id="correctCount">0</div>
                <div class="stat-label">정답</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="totalCount">0</div>
                <div class="stat-label">전체</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="accuracy">0%</div>
                <div class="stat-label">정답률</div>
            </div>
        </div>
        
        <!-- 시작 화면 -->
        <div id="startScreen" class="status">
            <h2>학습을 시작하시겠습니까?</h2>
            <p style="margin: 20px 0; color: #718096;">
                각 문제당 60초의 시간 제한이 있습니다.<br>
                상세한 해설을 읽고 다음 문제로 진행할 수 있습니다.
            </p>
            <button onclick="startLearning()">🚀 학습 시작</button>
        </div>
        
        <!-- 학습 컨텐츠 -->
        <div id="content" class="hidden">
            <div id="reading" class="reading-box"></div>
            
            <!-- 문제 1: 핵심어 -->
            <div id="question1" class="question-box hidden">
                <div class="question-header">
                    <span class="question-number">문제 1</span>
                    <span class="time-limit">⏱️ 시간 제한: 60초</span>
                </div>
                <p id="q1-stem" style="font-weight: bold; margin: 15px 0;"></p>
                <div id="q1-choices" class="choices"></div>
                <div class="button-container">
                    <button id="submitQ1" onclick="submitQ1()">답안 제출</button>
                </div>
                <div id="q1-explanation" class="explanation"></div>
                <div class="button-container">
                    <button id="nextQ1" class="next-button" onclick="goToQuestion(2)">다음 문제로 →</button>
                </div>
            </div>
            
            <!-- 문제 2: 중심 문장 -->
            <div id="question2" class="question-box hidden">
                <div class="question-header">
                    <span class="question-number">문제 2</span>
                    <span class="time-limit">⏱️ 시간 제한: 60초</span>
                </div>
                <p id="q2-stem" style="font-weight: bold; margin: 15px 0;"></p>
                <div id="q2-choices" class="choices"></div>
                <div class="button-container">
                    <button id="submitQ2" onclick="submitQ2()">답안 제출</button>
                </div>
                <div id="q2-explanation" class="explanation"></div>
                <div class="button-container">
                    <button id="nextQ2" class="next-button" onclick="goToQuestion(3)">다음 문제로 →</button>
                </div>
            </div>
            
            <!-- 문제 3: 주제 -->
            <div id="question3" class="question-box hidden">
                <div class="question-header">
                    <span class="question-number">문제 3</span>
                    <span class="time-limit">⏱️ 시간 제한: 90초</span>
                </div>
                <p id="q3-stem" style="font-weight: bold; margin: 15px 0;"></p>
                <textarea id="q3-answer" placeholder="이 문단의 주제를 한 문장으로 요약해주세요."></textarea>
                <div class="button-container">
                    <button id="submitQ3" onclick="submitQ3()">답안 제출</button>
                </div>
                <div id="q3-explanation" class="explanation"></div>
                <div class="button-container">
                    <button id="nextQ3" class="next-button" onclick="showComplete()">학습 완료 →</button>
                </div>
            </div>
            
            <!-- 완료 화면 -->
            <div id="complete" class="hidden">
                <div class="status">
                    <h2>🎉 학습 완료!</h2>
                    <div class="stats" style="margin: 30px auto; max-width: 400px;">
                        <div class="stat-item">
                            <div class="stat-value" id="finalCorrect">0</div>
                            <div class="stat-label">정답</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value" id="finalTotal">3</div>
                            <div class="stat-label">전체</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value" id="finalAccuracy">0%</div>
                            <div class="stat-label">정답률</div>
                        </div>
                    </div>
                    <button onclick="startLearning()">🔄 새 문제 풀기</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentTask = null;
        let currentQuestion = 0;
        let selectedAnswers = [null, null, null];
        let correctAnswers = [false, false, false];
        let timerInterval = null;
        let timeRemaining = 60;
        let questionSubmitted = [false, false, false];
        
        // 타이머 시작
        function startTimer(seconds) {
            clearInterval(timerInterval);
            timeRemaining = seconds;
            
            const timerEl = document.getElementById('timer');
            const timerFillEl = document.getElementById('timerFill');
            const timerContainer = document.getElementById('timerContainer');
            
            timerContainer.style.display = 'block';
            
            timerInterval = setInterval(() => {
                timeRemaining--;
                timerEl.textContent = timeRemaining;
                
                const percentage = (timeRemaining / seconds) * 100;
                timerFillEl.style.width = percentage + '%';
                
                // 색상 변경
                if (timeRemaining <= 10) {
                    timerEl.className = 'timer danger';
                    timerFillEl.style.background = 'linear-gradient(90deg, #fc8181 0%, #f56565 100%)';
                } else if (timeRemaining <= 30) {
                    timerEl.className = 'timer warning';
                    timerFillEl.style.background = 'linear-gradient(90deg, #f6ad55 0%, #ed8936 100%)';
                } else {
                    timerEl.className = 'timer';
                    timerFillEl.style.background = 'linear-gradient(90deg, #48bb78 0%, #38a169 100%)';
                }
                
                if (timeRemaining <= 0) {
                    clearInterval(timerInterval);
                    autoSubmit();
                }
            }, 1000);
        }
        
        // 시간 초과 시 자동 제출
        function autoSubmit() {
            const qNum = currentQuestion;
            if (!questionSubmitted[qNum - 1]) {
                if (qNum === 1) submitQ1(true);
                else if (qNum === 2) submitQ2(true);
                else if (qNum === 3) submitQ3(true);
            }
        }
        
        // 진행률 업데이트
        function updateProgress() {
            const progress = (currentQuestion / 3) * 100;
            document.getElementById('progress').style.width = progress + '%';
        }
        
        // 학습 시작
        function startLearning() {
            console.log('학습 시작...');
            
            // 초기화
            selectedAnswers = [null, null, null];
            correctAnswers = [false, false, false];
            questionSubmitted = [false, false, false];
            currentQuestion = 0;
            
            document.getElementById('startScreen').className = 'hidden';
            document.getElementById('complete').className = 'hidden';
            document.getElementById('stats').className = 'stats hidden';
            
            // 해설과 다음 버튼 숨기기
            document.querySelectorAll('.explanation').forEach(el => {
                el.className = 'explanation';
            });
            document.querySelectorAll('.next-button').forEach(el => {
                el.className = 'next-button';
            });
            
            // 버튼 활성화
            document.getElementById('submitQ1').disabled = false;
            document.getElementById('submitQ2').disabled = false;
            document.getElementById('submitQ3').disabled = false;
            
            fetch('/get_task', {
                method: 'GET'
            })
            .then(response => response.json())
            .then(data => {
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
        
        // 태스크 로드
        function loadTask() {
            if (!currentTask) return;
            
            // 읽기 자료 표시 (새 JSON 스키마에 맞게 수정)
            let content = '';
            if (currentTask.task_type === 'paragraph') {
                // 새 스키마: content 필드 사용
                content = currentTask.content || currentTask.paragraph?.text || '';
            } else {
                // article의 경우도 content 필드를 먼저 확인
                if (currentTask.content) {
                    content = currentTask.content;
                } else if (currentTask.article?.paragraphs) {
                    content = currentTask.article.paragraphs.map(p => 
                        typeof p === 'string' ? p : p.text
                    ).join('<br><br>');
                }
            }
            document.getElementById('reading').innerHTML = content;
            
            // 문제 1: 핵심어 (새 JSON 스키마에 맞게 수정)
            const q1 = currentTask.q_keywords_mcq;
            document.getElementById('q1-stem').textContent = q1.question || q1.stem || '이 문단의 핵심 키워드는 무엇입니까?';
            const choices = q1.options || q1.choices || [];
            
            // 디버깅: choices의 내용 확인
            console.log('choices:', choices);
            choices.forEach((choice, i) => {
                console.log(`choice ${i}:`, typeof choice, choice);
            });
            
            document.getElementById('q1-choices').innerHTML = choices.map((choice, i) => {
                // choice가 객체인 경우 text 속성을 사용, 아니면 문자열 그대로 사용
                const choiceText = typeof choice === 'object' ? (choice.text || choice.content || JSON.stringify(choice)) : choice;
                return `<div class="choice" onclick="selectChoice(1, ${i})" data-index="${i}">${i+1}. ${choiceText}</div>`;
            }).join('');
            
            // 문제 2: 중심 문장 (새 JSON 스키마에 맞게 수정)
            const q2 = currentTask.q_center_sentence_mcq || currentTask.q_center_paragraph_mcq;
            document.getElementById('q2-stem').textContent = q2.question || q2.stem || '이 문단의 중심 문장은 무엇입니까?';
            const choices2 = q2.options || q2.choices || [];
            
            // 디버깅: choices2의 내용 확인
            console.log('choices2:', choices2);
            choices2.forEach((choice, i) => {
                console.log(`choice ${i}:`, typeof choice, choice);
            });
            
            document.getElementById('q2-choices').innerHTML = choices2.map((choice, i) => {
                // choice가 객체인 경우 text 속성을 사용, 아니면 문자열 그대로 사용
                const choiceText = typeof choice === 'object' ? (choice.text || choice.content || JSON.stringify(choice)) : choice;
                return `<div class="choice" onclick="selectChoice(2, ${i})" data-index="${i}">${choiceText}</div>`;
            }).join('');
            
            // 문제 3: 주제
            const q3 = currentTask.q_topic_free;
            document.getElementById('q3-stem').textContent = q3.question || '이 문단의 주제를 한 문장으로 요약하세요.';
            document.getElementById('q3-answer').value = '';
            
            // 화면 표시
            document.getElementById('content').className = '';
            document.getElementById('stats').className = 'stats';
            updateStats();
            goToQuestion(1);
        }
        
        // 선택지 선택
        function selectChoice(questionNum, choiceIndex) {
            if (questionSubmitted[questionNum - 1]) return;
            
            const container = document.getElementById(`q${questionNum}-choices`);
            container.querySelectorAll('.choice').forEach(c => c.classList.remove('selected'));
            container.querySelector(`[data-index="${choiceIndex}"]`).classList.add('selected');
            selectedAnswers[questionNum - 1] = choiceIndex;
        }
        
        // 문제 이동
        function goToQuestion(qNum) {
            [1, 2, 3].forEach(i => {
                document.getElementById(`question${i}`).className = 'question-box hidden';
            });
            
            if (qNum <= 3) {
                document.getElementById(`question${qNum}`).className = 'question-box';
                currentQuestion = qNum;
                updateProgress();
                
                // 타이머 시작
                const timeLimit = qNum === 3 ? 90 : 60;
                startTimer(timeLimit);
            }
        }
        
        // 문제 1 제출
        function submitQ1(isTimeout = false) {
            if (questionSubmitted[0]) return;
            
            if (!isTimeout && selectedAnswers[0] === null) {
                alert('답을 선택해주세요.');
                return;
            }
            
            clearInterval(timerInterval);
            questionSubmitted[0] = true;
            document.getElementById('submitQ1').disabled = true;
            
            const answer = isTimeout ? -1 : selectedAnswers[0];
            
            fetch('/submit_answer', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    task_id: currentTask.id,
                    question_type: 'keywords',
                    answer: answer,
                    is_timeout: isTimeout
                })
            })
            .then(response => response.json())
            .then(data => {
                correctAnswers[0] = data.correct;
                showExplanation(1, data.correct, data.explanation);
                updateStats();
                
                // 선택지 색상 표시
                const choices = document.getElementById('q1-choices').querySelectorAll('.choice');
                if (answer >= 0) {
                    choices[answer].classList.add(data.correct ? 'correct' : 'incorrect');
                }
                if (!data.correct && data.correct_index !== undefined) {
                    choices[data.correct_index].classList.add('correct');
                }
            });
        }
        
        // 문제 2 제출
        function submitQ2(isTimeout = false) {
            if (questionSubmitted[1]) return;
            
            if (!isTimeout && selectedAnswers[1] === null) {
                alert('답을 선택해주세요.');
                return;
            }
            
            clearInterval(timerInterval);
            questionSubmitted[1] = true;
            document.getElementById('submitQ2').disabled = true;
            
            const answer = isTimeout ? -1 : selectedAnswers[1];
            
            fetch('/submit_answer', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    task_id: currentTask.id,
                    question_type: 'center',
                    answer: answer,
                    is_timeout: isTimeout
                })
            })
            .then(response => response.json())
            .then(data => {
                correctAnswers[1] = data.correct;
                showExplanation(2, data.correct, data.explanation);
                updateStats();
                
                // 선택지 색상 표시
                const choices = document.getElementById('q2-choices').querySelectorAll('.choice');
                if (answer >= 0) {
                    choices[answer].classList.add(data.correct ? 'correct' : 'incorrect');
                }
                if (!data.correct && data.correct_index !== undefined) {
                    choices[data.correct_index].classList.add('correct');
                }
            });
        }
        
        // 문제 3 제출
        function submitQ3(isTimeout = false) {
            if (questionSubmitted[2]) return;
            
            const answer = document.getElementById('q3-answer').value.trim();
            
            if (!isTimeout && !answer) {
                alert('답을 작성해주세요.');
                return;
            }
            
            clearInterval(timerInterval);
            questionSubmitted[2] = true;
            document.getElementById('submitQ3').disabled = true;
            
            fetch('/submit_answer', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    task_id: currentTask.id,
                    question_type: 'topic',
                    answer: isTimeout ? '' : answer,
                    is_timeout: isTimeout
                })
            })
            .then(response => response.json())
            .then(data => {
                correctAnswers[2] = data.correct;
                showExplanation(3, data.correct, data.explanation);
                updateStats();
            });
        }
        
        // 해설 표시
        function showExplanation(qNum, correct, explanation) {
            const explEl = document.getElementById(`q${qNum}-explanation`);
            explEl.innerHTML = explanation;
            explEl.className = 'explanation show';
            
            // 다음 버튼 표시
            document.getElementById(`nextQ${qNum}`).className = 'next-button show';
            
            // 타이머 숨기기
            document.getElementById('timerContainer').style.display = 'none';
        }
        
        // 통계 업데이트
        function updateStats() {
            const correct = correctAnswers.filter(c => c).length;
            const total = questionSubmitted.filter(s => s).length;
            const accuracy = total > 0 ? Math.round((correct / total) * 100) : 0;
            
            document.getElementById('correctCount').textContent = correct;
            document.getElementById('totalCount').textContent = total;
            document.getElementById('accuracy').textContent = accuracy + '%';
        }
        
        // 완료 화면
        function showComplete() {
            document.getElementById('question3').className = 'question-box hidden';
            document.getElementById('complete').className = '';
            
            const correct = correctAnswers.filter(c => c).length;
            const accuracy = Math.round((correct / 3) * 100);
            
            document.getElementById('finalCorrect').textContent = correct;
            document.getElementById('finalTotal').textContent = '3';
            document.getElementById('finalAccuracy').textContent = accuracy + '%';
            
            updateProgress();
        }
        
        console.log('개선된 학습 시스템 준비 완료');
    </script>
</body>
</html>
"""


class EnhancedLearningSystem:
    def __init__(self):
        self.tasks = self.load_tasks()
        self.used_tasks = set()
    
    def load_tasks(self):
        tasks = []
        # Load files from parallel_sets directory (all sets)
        json_files = []
        json_files.extend(glob.glob("generator/parallel_sets/**/*.json", recursive=True))
        
        # Fallback: also try old directories for backward compatibility
        json_files.extend(glob.glob("generator/set_1/**/*.json", recursive=True))
        json_files.extend(glob.glob("generator/set_2/**/*.json", recursive=True))
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    task = json.load(f)
                    # Ensure compatibility: add 'id' field if missing
                    if 'id' not in task and 'task_id' in task:
                        task['id'] = task['task_id']
                    elif 'id' not in task:
                        # Generate ID from filename if no task_id
                        import os
                        task['id'] = os.path.basename(file_path).replace('.json', '')
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
        print(f"[DEBUG] 유사도 계산 시작:", flush=True)
        print(f"[DEBUG] text1: '{text1}' (타입: {type(text1)})", flush=True)
        print(f"[DEBUG] text2: '{text2}' (타입: {type(text2)})", flush=True)
        
        words1 = re.findall(r'[가-힣]+', text1.lower())
        words2 = re.findall(r'[가-힣]+', text2.lower())
        
        print(f"[DEBUG] words1: {words1}")
        print(f"[DEBUG] words2: {words2}")
        
        if not words1 or not words2:
            print(f"[DEBUG] words1 또는 words2가 비어있음 -> 0.0 반환")
            return 0.0
        
        counter1 = Counter(words1)
        counter2 = Counter(words2)
        
        print(f"[DEBUG] counter1: {counter1}")
        print(f"[DEBUG] counter2: {counter2}")
        
        all_words = set(counter1.keys()) | set(counter2.keys())
        
        dot_product = sum(counter1.get(word, 0) * counter2.get(word, 0) for word in all_words)
        magnitude1 = math.sqrt(sum(count ** 2 for count in counter1.values()))
        magnitude2 = math.sqrt(sum(count ** 2 for count in counter2.values()))
        
        print(f"[DEBUG] dot_product: {dot_product}")
        print(f"[DEBUG] magnitude1: {magnitude1}")
        print(f"[DEBUG] magnitude2: {magnitude2}")
        
        if magnitude1 == 0 or magnitude2 == 0:
            print(f"[DEBUG] magnitude가 0 -> 0.0 반환")
            return 0.0
        
        similarity = dot_product / (magnitude1 * magnitude2)
        print(f"[DEBUG] 최종 유사도: {similarity}")
        return similarity
    
    def generate_explanation(self, task, question_type, user_answer, correct):
        """상세한 해설 생성"""
        
        # 텍스트 추출 (paragraph 또는 article - 새로운 스키마 호환)
        if task['task_type'] == 'paragraph':
            # 새로운 스키마는 'content' 필드 사용, 구 스키마는 'paragraph.text' 사용
            if 'content' in task:
                text_content = task['content']
            else:
                text_content = task['paragraph']['text']
        else:
            # 새로운 스키마는 'content' 필드 사용, 구 스키마는 'article.paragraphs' 사용
            if 'content' in task:
                text_content = task['content']
            else:
                paragraphs = task['article']['paragraphs']
                if isinstance(paragraphs[0], dict):
                    text_content = ' '.join([p['text'] for p in paragraphs])
                else:
                    text_content = ' '.join(paragraphs)
        
        if question_type == 'keywords':
            q = task['q_keywords_mcq']
            # 새로운 스키마 호환: 'answer' vs 'answer_index', 'options' vs 'choices'
            correct_idx = q.get('answer', q.get('answer_index', q.get('correct_index', 0)))
            choices = q.get('options', q.get('choices', []))
            if choices and len(choices) > correct_idx:
                correct_answer = choices[correct_idx]
            else:
                correct_answer = "정답을 찾을 수 없습니다"
            
            explanation = f"""
            <div class="explanation-header">📚 핵심어 문제 해설</div>
            <div class="explanation-content">
                <div class="explanation-section">
                    <div class="explanation-label">✅ 정답:</div>
                    <strong>{correct_answer}</strong>
                </div>
                
                <div class="explanation-section">
                    <div class="explanation-label">💡 해설:</div>
                    핵심어는 글 전체를 관통하는 가장 중요한 개념입니다.<br>
                    "{correct_answer}"는 이 문단의 모든 내용이 이를 중심으로 전개되고 있기 때문에 핵심어입니다.
                </div>
                
                <div class="explanation-section">
                    <div class="explanation-label">❌ 오답 분석:</div>
            """
            
            # 새로운 스키마 호환으로 위에서 이미 choices 변수를 설정했음
            for i, choice in enumerate(choices):
                if i != correct_idx:
                    if choice in text_content:
                        explanation += f"• <strong>{choice}</strong>: 문단에 등장하지만 부수적인 개념입니다.<br>"
                    else:
                        explanation += f"• <strong>{choice}</strong>: 관련 있지만 핵심 개념은 아닙니다.<br>"
            
            explanation += """
                </div>
                
                <div class="explanation-section">
                    <div class="explanation-label">📌 학습 포인트:</div>
                    핵심어를 찾을 때는 반복되거나 다른 내용들이 이를 설명하는 중심 개념을 찾아야 합니다.
                </div>
            </div>
            """
            
            return explanation
        
        elif question_type == 'center':
            if task['task_type'] == 'paragraph':
                q = task['q_center_sentence_mcq']
            else:
                q = task['q_center_paragraph_mcq']
            
            # 새로운 스키마 호환: 'answer' vs 'answer_idx'/'answer_index', 'options' vs 'choices'
            correct_idx = q.get('answer', q.get('answer_idx', q.get('answer_index', 0)))
            choices = q.get('options', q.get('choices', []))
            if choices and len(choices) > correct_idx:
                correct_answer = choices[correct_idx]
            else:
                correct_answer = "정답을 찾을 수 없습니다"
            
            explanation = f"""
            <div class="explanation-header">📖 중심 문장 문제 해설</div>
            <div class="explanation-content">
                <div class="explanation-section">
                    <div class="explanation-label">✅ 정답:</div>
                    <strong>{correct_answer}</strong>
                </div>
                
                <div class="explanation-section">
                    <div class="explanation-label">💡 해설:</div>
                    중심 문장은 문단의 핵심 주제를 담고 있는 문장입니다.<br>
                    이 문장이 중심 문장인 이유는 다른 문장들이 이를 뒷받침하거나 구체화하기 때문입니다.
                </div>
                
                <div class="explanation-section">
                    <div class="explanation-label">📌 문단 구조 분석:</div>
                    • 도입부: 주제 제시<br>
                    • 전개부: 구체적 설명과 예시<br>
                    • 결론부: 핵심 내용 정리<br>
                    중심 문장은 주로 첫 문장이나 마지막 문장에 위치합니다.
                </div>
            </div>
            """
            
            return explanation
        
        elif question_type == 'topic':
            q = task['q_topic_free']
            target = q.get('target_answer', q.get('target_topic', ''))
            
            if user_answer:
                similarity = self.calculate_similarity(user_answer, target)
                similarity_percent = int(similarity * 100)
            else:
                similarity_percent = 0
            
            explanation = f"""
            <div class="explanation-header">✍️ 주제 파악 문제 해설</div>
            <div class="explanation-content">
                <div class="explanation-section">
                    <div class="explanation-label">📝 모범 답안:</div>
                    <strong>{target}</strong>
                </div>
                
                <div class="explanation-section">
                    <div class="explanation-label">📊 당신의 답변 분석:</div>
                    유사도: <strong>{similarity_percent}%</strong><br>
                    {"시간 초과로 답변을 작성하지 못했습니다." if not user_answer else 
                     "좋은 답변입니다!" if similarity_percent >= 30 else 
                     "핵심 키워드가 부족합니다."}
                </div>
                
                <div class="explanation-section">
                    <div class="explanation-label">💡 주제 요약 팁:</div>
                    • 핵심 키워드를 포함시키세요<br>
                    • 구체적이고 명확하게 표현하세요<br>
                    • 한 문장으로 간결하게 정리하세요<br>
                    • 글의 전체 내용을 포괄하는 표현을 사용하세요
                </div>
                
                <div class="explanation-section">
                    <div class="explanation-label">📌 필수 포함 키워드:</div>
                    {', '.join(q.get('evaluation_criteria', {}).get('required_keywords', []))}
                </div>
            </div>
            """
            
            return explanation
        
        return "해설을 생성할 수 없습니다."


system = EnhancedLearningSystem()

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/get_task')
def get_task():
    task = system.get_random_task()
    if task:
        print(f"[DEBUG] 로드된 태스크 ID: {task['id']}")
        # Content 필드 호환성 처리
        if 'content' in task:
            content = task['content']
        elif 'paragraph' in task and 'text' in task['paragraph']:
            content = task['paragraph']['text']
        elif 'article' in task and 'paragraphs' in task['article']:
            content = ' '.join(task['article']['paragraphs'])
        else:
            content = 'No content found'
            
        if isinstance(content, str):
            print(f"[DEBUG] 태스크 내용: {content[:100]}...")
        else:
            print(f"[DEBUG] 태스크 내용: {str(content)[:100]}...")
            
        # Options 필드 호환성 처리
        q_keywords = task.get('q_keywords_mcq', {})
        keywords_options = q_keywords.get('options', q_keywords.get('choices', 'No options'))
        keywords_answer = q_keywords.get('answer', q_keywords.get('answer_index', 'No answer'))
        
        print(f"[DEBUG] 핵심어 선택지: {keywords_options}")
        print(f"[DEBUG] 핵심어 정답: {keywords_answer}")
        print(f"[DEBUG] 전체 태스크 구조: {list(task.keys())}")
        print(f"Serving task: {task['id']}")
        return jsonify({'success': True, 'task': task})
    return jsonify({'success': False, 'message': 'No tasks available'})

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = request.json
    
    print(f"[DEBUG] submit_answer 호출됨", flush=True)
    print(f"[DEBUG] 받은 데이터: {data}", flush=True)
    task_id = data['task_id']
    question_type = data['question_type']
    answer = data['answer']
    is_timeout = data.get('is_timeout', False)
    
    # Find task
    task = None
    for t in system.tasks:
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
            
            # 디버깅 출력 추가
            print(f"[DEBUG] 객관식 키워드 문제:", flush=True)
            options = q.get('options', q.get('choices', 'No options'))
            print(f"[DEBUG] 선택지: {options}", flush=True)
            print(f"[DEBUG] JSON 정답 (1-based): {original_correct_index}", flush=True)
            print(f"[DEBUG] 사용자 답 (0-based): {answer}", flush=True)
            
            # parallel_sets JSON은 1-based index를 사용하지만 프론트엔드는 0-based를 전송
            # 1-based를 0-based로 변환하여 비교
            correct_index = original_correct_index
            if correct_index > 0:  # 1-based인 경우
                correct_index = correct_index - 1
                
            print(f"[DEBUG] 변환된 정답 (0-based): {correct_index}", flush=True)
            print(f"[DEBUG] 비교 결과: {answer} == {correct_index} = {answer == correct_index}", flush=True)
            
            correct = (answer == correct_index)
        
        elif question_type == 'center':
            if task['task_type'] == 'paragraph':
                q = task['q_center_sentence_mcq']
            else:
                q = task['q_center_paragraph_mcq']
            
            original_correct_index = q.get('answer', q.get('answer_idx', q.get('answer_index', 0)))
            
            # 디버깅 출력 추가
            print(f"[DEBUG] 객관식 중심문장/문단 문제:", flush=True)
            options = q.get('options', q.get('choices', 'No options'))
            print(f"[DEBUG] 선택지: {options}", flush=True)
            print(f"[DEBUG] JSON 정답 (1-based): {original_correct_index}", flush=True)
            print(f"[DEBUG] 사용자 답 (0-based): {answer}", flush=True)
            
            # parallel_sets JSON은 1-based index를 사용하지만 프론트엔드는 0-based를 전송  
            # 1-based를 0-based로 변환하여 비교
            correct_index = original_correct_index
            if correct_index > 0:  # 1-based인 경우
                correct_index = correct_index - 1
                
            print(f"[DEBUG] 변환된 정답 (0-based): {correct_index}", flush=True)
            print(f"[DEBUG] 비교 결과: {answer} == {correct_index} = {answer == correct_index}", flush=True)
                
            correct = (answer == correct_index)
        
        elif question_type == 'topic':
            if answer:
                q = task['q_topic_free']
                # 새로운 스키마 호환: 'answer' vs 'target_answer'/'target_topic' 
                target = q.get('answer', q.get('target_answer', q.get('target_topic', '')))
                
                # 디버깅 로그 추가
                print(f"[DEBUG] 자유응답 비교:", flush=True)
                print(f"[DEBUG] 사용자 답안: '{answer}'", flush=True)
                print(f"[DEBUG] 모범 답안: '{target}'", flush=True)
                print(f"[DEBUG] 전체 q_topic_free: {q}", flush=True)
                
                similarity = system.calculate_similarity(answer, target)
                print(f"[DEBUG] 계산된 유사도: {similarity}", flush=True)
                correct = similarity >= 0.3
            else:
                correct = False
    
    # 상세한 해설 생성
    explanation = system.generate_explanation(task, question_type, answer, correct)
    
    return jsonify({
        'success': True,
        'correct': correct,
        'correct_index': correct_index,
        'explanation': explanation
    })

if __name__ == '__main__':
    print(f"Enhanced Korean Reading System")
    print(f"Tasks loaded: {len(system.tasks)}")
    if system.tasks:
        print("Sample tasks:", [t['id'] for t in system.tasks[:3]])
    
    app.run(host='0.0.0.0', port=8080, debug=True)