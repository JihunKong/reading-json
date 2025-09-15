#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 한국어 독해 학습 웹 애플리케이션
- 다양한 주제로 문제 생성
- 주제 요약 문제 제공
- 정답과 피드백 표시
"""

from flask import Flask, request, jsonify, render_template
import random
import json
import os
from datetime import datetime
import requests

app = Flask(__name__)

# Upstage API 설정
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
UPSTAGE_BASE_URL = os.getenv("UPSTAGE_BASE_URL", "https://api.upstage.ai/v1")
UPSTAGE_MODEL = os.getenv("UPSTAGE_MODEL", "solar-pro2")

def call_upstage_api(prompt, max_tokens=500):
    """Upstage API를 호출하여 텍스트 생성"""
    if not UPSTAGE_API_KEY:
        return None

    try:
        headers = {
            "Authorization": f"Bearer {UPSTAGE_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": UPSTAGE_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }

        response = requests.post(
            f"{UPSTAGE_BASE_URL}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        else:
            print(f"Upstage API 오류: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"Upstage API 호출 중 오류: {e}")
        return None

def generate_ai_task():
    """AI를 사용하여 새로운 학습 문제 생성"""
    prompt = """한국어 독해 학습을 위한 문제를 생성해주세요.

요구사항:
1. 3-4개 문장으로 구성된 짧은 문단 작성
2. 고등학생 수준에 맞는 내용
3. 명확한 주제가 있는 설명문 형식
4. 문단의 주제를 한 문장으로 요약할 수 있는 모범답안 제시

주제는 다음 중 하나를 선택: 환경보호, 디지털기술, 전통문화, 교육, 소통, 건강, 경제, 사회문제

JSON 형식으로 응답해주세요:
{
  "topic": "주제명",
  "sentences": ["문장1", "문장2", "문장3", "문장4"],
  "target_answer": "주제 요약 모범답안"
}"""

    ai_response = call_upstage_api(prompt, max_tokens=800)

    if ai_response:
        try:
            # JSON 추출 시도
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                ai_data = json.loads(json_match.group())
                return ai_data
        except Exception as e:
            print(f"AI 응답 파싱 오류: {e}")

    return None

def generate_new_task():
    """새로운 학습 문제를 생성합니다."""

    # AI 생성 시도 (우선순위)
    if UPSTAGE_API_KEY:
        ai_task = generate_ai_task()
        if ai_task:
            # AI 생성 성공 시 구조화된 응답 생성
            task = {
                "task_id": f"ai_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}",
                "task_type": "paragraph",
                "difficulty": "medium",
                "topic": ai_task.get("topic", "일반"),
                "paragraph": {
                    "text": " ".join(ai_task.get("sentences", [])),
                    "sentences": ai_task.get("sentences", [])
                },
                "target_answer": ai_task.get("target_answer", ""),
                "q_topic_free": {
                    "stem": "위 글의 주제를 한 문장으로 요약해서 작성해주세요.",
                    "scoring": {
                        "method": "similarity",
                        "target": ai_task.get("target_answer", ""),
                        "required_elements": ["주제", "핵심내용"],
                        "similarity_threshold": 0.6
                    }
                }
            }
            return task

    # AI 실패 시 로컬 템플릿 사용 (백업)
    # 다양한 주제 템플릿
    topic_templates = [
        {
            "topic": "환경 보호",
            "sentences": [
                "환경 보호는 기후 변화와 생태계 파괴에 대응하기 위해 필수적이다.",
                "재활용, 에너지 절약, 친환경 제품 사용 등의 일상적인 실천이 중요하다.",
                "정부와 기업도 환경 규제 강화와 녹색 기술 개발에 앞장서고 있다.",
                "개인과 사회 전체가 함께 노력할 때 지속 가능한 미래를 만들 수 있다."
            ],
            "target_answer": "환경 보호는 기후 변화와 생태계 파괴에 대응하기 위해 개인의 일상적 실천과 정부·기업의 제도적 노력이 함께 필요한 중요한 과제이다."
        },
        {
            "topic": "디지털 기술의 발전",
            "sentences": [
                "디지털 기술의 급속한 발전이 우리 삶의 모든 영역을 변화시키고 있다.",
                "스마트폰, 인공지능, 사물인터넷 등이 일상생활을 더욱 편리하게 만들어주고 있다.",
                "교육, 의료, 금융 분야에서도 디지털 혁신이 새로운 가능성을 열어주고 있다.",
                "하지만 디지털 격차와 개인정보 보호 등의 문제도 동시에 해결해야 한다."
            ],
            "target_answer": "디지털 기술의 급속한 발전이 생활의 편의성과 각 분야의 혁신을 가져왔지만, 디지털 격차와 개인정보 보호 등의 과제도 함께 해결해야 한다."
        },
        {
            "topic": "전통문화의 계승",
            "sentences": [
                "전통문화는 한 민족의 정체성을 나타내는 소중한 유산이다.",
                "현대사회에서 전통문화가 점차 사라져가는 것은 심각한 문제이다.",
                "젊은 세대에게 전통문화의 가치를 알리고 체험할 기회를 제공해야 한다.",
                "전통과 현대의 조화를 통해 문화의 지속가능한 발전을 도모해야 한다."
            ],
            "target_answer": "전통문화는 민족 정체성을 나타내는 소중한 유산으로, 젊은 세대에게 그 가치를 알리고 전통과 현대의 조화를 통한 지속가능한 발전이 필요하다."
        },
        {
            "topic": "평생학습의 중요성",
            "sentences": [
                "빠르게 변화하는 현대사회에서 평생학습은 필수적인 역량이 되었다.",
                "새로운 기술과 지식을 지속적으로 습득해야 경쟁력을 유지할 수 있다.",
                "온라인 교육 플랫폼의 발달로 누구나 쉽게 학습할 수 있는 환경이 조성되었다.",
                "개인의 성장과 사회 발전을 위해 평생학습 문화가 확산되어야 한다."
            ],
            "target_answer": "빠르게 변화하는 현대사회에서 경쟁력 유지와 개인 성장을 위해 새로운 기술과 지식을 지속적으로 습득하는 평생학습이 필수적이다."
        },
        {
            "topic": "소통의 중요성",
            "sentences": [
                "효과적인 소통은 인간관계의 기본이자 사회 발전의 원동력이다.",
                "상대방의 입장을 이해하고 공감하는 자세가 좋은 소통의 출발점이다.",
                "디지털 시대에도 진정성 있는 대화와 경청의 중요성은 변하지 않는다.",
                "갈등을 해결하고 협력을 증진하기 위해서는 열린 마음의 소통이 필요하다."
            ],
            "target_answer": "효과적인 소통은 상대방에 대한 이해와 공감, 진정성 있는 대화와 경청을 바탕으로 인간관계와 사회 발전의 기초가 되는 중요한 능력이다."
        }
    ]

    # 랜덤하게 주제 선택
    selected_template = random.choice(topic_templates)

    # 문제 구조 생성
    task = {
        "task_id": f"topic_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}",
        "task_type": "paragraph",
        "difficulty": "medium",
        "topic": selected_template["topic"],
        "paragraph": {
            "text": " ".join(selected_template["sentences"]),
            "sentences": selected_template["sentences"]
        },
        "target_answer": selected_template["target_answer"],
        "q_topic_free": {
            "stem": "위 글의 주제를 한 문장으로 요약해서 작성해주세요.",
            "scoring": {
                "method": "similarity",
                "target": selected_template["target_answer"],
                "required_elements": ["주제", "핵심내용"],
                "similarity_threshold": 0.6
            }
        }
    }

    return task

def grade_topic_free(user_answer, task):
    """주제 요약 문제 채점"""
    target_answer = task.get("target_answer", "")

    # 간단한 키워드 기반 채점
    user_words = set(user_answer.replace(" ", "").replace(".", "").replace(",", ""))
    target_words = set(target_answer.replace(" ", "").replace(".", "").replace(",", ""))

    # 공통 문자 수 계산
    common_chars = len(user_words.intersection(target_words))
    total_chars = len(target_words)

    if total_chars == 0:
        similarity = 0
    else:
        similarity = common_chars / total_chars

    # 점수 계산 (0-100점)
    score = min(100, max(0, similarity * 100))

    # 점수별 피드백
    if score >= 80:
        score_feedback = "excellent! 훌륭한 요약입니다."
        is_correct = True
    elif score >= 60:
        score_feedback = "good! 주요 내용을 잘 파악했습니다."
        is_correct = True
    elif score >= 40:
        score_feedback = "보통입니다. 핵심 내용을 더 포함해보세요."
        is_correct = False
    else:
        score_feedback = "아쉽습니다. 글의 주제를 다시 파악해보세요."
        is_correct = False

    # 구조화된 피드백 생성
    feedback = f"📋 점수: {score:.1f}점\n\n📝 모범답안: {target_answer}\n\n💬 피드백: {score_feedback}\n\n💡 개선방향: 글의 핵심 내용과 주제의식을 명확하게 드러내는 문장으로 요약해보세요."

    return {
        "score": score,
        "correct": is_correct,
        "feedback": feedback,
        "similarity": similarity
    }

@app.route('/')
def index():
    """메인 페이지"""
    try:
        return render_template('simple_study.html')
    except Exception as e:
        # 템플릿 없을 경우 간단한 HTML 반환
        return f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>한국어 독해 학습</title>
        </head>
        <body>
            <h1>한국어 독해 학습 시스템</h1>
            <p>템플릿 로딩 오류: {str(e)}</p>
            <p>API 테스트: <a href="/api/get_task">문제 생성 테스트</a></p>
        </body>
        </html>
        """

@app.route('/api/get_task', methods=['GET', 'POST'])
def get_task():
    """새로운 학습 문제 제공"""
    try:
        data = request.get_json() or {}
        task = generate_new_task()

        if request.method == 'GET':
            # GET 요청 시 간단한 테스트 응답
            return f"""
            <h2>API 테스트 성공!</h2>
            <p>생성된 문제:</p>
            <pre>{json.dumps(task, ensure_ascii=False, indent=2)}</pre>
            <p><a href="/">메인 페이지로 돌아가기</a></p>
            """

        return jsonify({
            "success": True,
            "task": task,
            "message": "새로운 문제가 생성되었습니다."
        })
    except Exception as e:
        error_msg = f"문제 생성 중 오류가 발생했습니다: {str(e)}"
        if request.method == 'GET':
            return f"<h2>오류 발생</h2><p>{error_msg}</p>"
        return jsonify({
            "success": False,
            "message": error_msg
        }), 500

@app.route('/api/submit_answer', methods=['POST'])
def submit_answer():
    """답안 제출 및 채점"""
    try:
        data = request.get_json()
        task = data.get('task')
        question_type = data.get('question_type')
        answer = data.get('answer')

        if not task or not question_type or not answer:
            return jsonify({
                "success": False,
                "message": "필수 정보가 누락되었습니다."
            }), 400

        if question_type == 'topic':
            result = grade_topic_free(answer, task)
            return jsonify({
                "success": True,
                "correct": result["correct"],
                "score": result["score"],
                "feedback": result["feedback"],
                "similarity": result["similarity"]
            })
        else:
            return jsonify({
                "success": False,
                "message": "지원하지 않는 문제 유형입니다."
            }), 400

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"채점 중 오류가 발생했습니다: {str(e)}"
        }), 500

# Vercel을 위한 WSGI 진입점
app_instance = app

if __name__ == '__main__':
    # 템플릿 디렉토리 확인
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    if not os.path.exists(template_dir):
        os.makedirs(template_dir)
        print(f"템플릿 디렉토리를 생성했습니다: {template_dir}")

    print("🚀 한국어 독해 학습 시스템을 시작합니다...")
    print("📖 다양한 주제의 문제가 제공됩니다:")
    print("   - 환경 보호")
    print("   - 디지털 기술의 발전")
    print("   - 전통문화의 계승")
    print("   - 평생학습의 중요성")
    print("   - 소통의 중요성")
    print("🌐 http://localhost:5000 에서 학습을 시작하세요!")

    app.run(debug=True, host='0.0.0.0', port=5000)