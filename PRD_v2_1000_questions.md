# PRD v2: Korean Reading Comprehension System (1000 Questions Scale)

## 1. Executive Summary

### Vision
1000개의 고품질 한국어 독해 문제를 생성하고, 자동 품질 평가를 통해 최상위 문제만을 선별하여 학생들에게 랜덤으로 출제하는 완전 자동화된 교육 시스템

### Key Objectives
- **규모**: 1000개 문제 생성 (10세트 × 100문제)
- **품질**: 70점 이상 자동 선별 (예상 700-800개)
- **자동화**: 병렬 생성, 자동 평가, 랜덤 출제
- **교육 효과**: 개인화된 학습 경로 제공

## 2. System Architecture

### 2.1 Core Components
```
┌──────────────────────────────────────────────────────────┐
│                     Orchestration Layer                    │
│  (Task Queue: Celery + RabbitMQ, Parallel Processing)     │
└──────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Generator Pool │  │ Validator Pool  │  │  Selector Pool  │
│   (3 Workers)   │  │   (2 Workers)   │  │   (1 Worker)    │
│                 │  │                 │  │                 │
│ - Upstage Solar │  │ - Quality Check │  │ - Best Select   │
│ - JSON Schema   │  │ - Score Calc    │  │ - Ranking       │
│ - Batch Process │  │ - Validation    │  │ - DB Storage    │
└─────────────────┘  └─────────────────┘  └─────────────────┘
        │                     │                     │
        └─────────────────────┴─────────────────────┘
                              │
                     ┌────────▼────────┐
                     │   PostgreSQL    │
                     │   + Redis Cache │
                     └────────┬────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Student Portal │  │ Teacher Dashboard│ │  Analytics API  │
│   (React SPA)   │  │   (Vue.js App)  │  │  (FastAPI REST) │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 2.2 Data Flow
1. **Generation Phase**: Parallel generation using Upstage Solar Pro2
2. **Validation Phase**: Multi-criteria quality assessment
3. **Selection Phase**: Top-tier problems selection (>70 points)
4. **Distribution Phase**: Random quiz generation per student
5. **Analytics Phase**: Performance tracking and insights

## 3. Content Specifications

### 3.1 Question Distribution (1000 Total)
```
문제 유형별 분포:
├── 문단 (Paragraph): 600개 (60%)
│   ├── Easy: 180개 (30%)
│   ├── Medium: 240개 (40%)
│   └── Hard: 180개 (30%)
└── 글 (Article): 400개 (40%)
    ├── Easy: 120개 (30%)
    ├── Medium: 160개 (40%)
    └── Hard: 120개 (30%)
```

### 3.2 Topic Coverage (Per Set of 100)
```
주제별 분포:
├── 교육/학습: 20개
├── 환경/생태: 20개
├── 기술/과학: 20개
├── 사회/문화: 20개
└── 건강/생활: 20개
```

### 3.3 Question Types
1. **핵심어 파악** (Keywords MCQ)
   - 4개 선택지
   - 지문의 중심 개념 식별

2. **중심문장/문단 파악** (Center Identification)
   - 5개 선택지 (마지막: "드러나지 않음")
   - 구조적 독해 능력 평가

3. **주제 서술** (Topic Writing)
   - 자유 응답
   - 유사도 기반 자동 채점

## 4. Quality Evaluation System

### 4.1 Quality Metrics (각 10점 만점, 총 100점)

#### 교육적 측면 (40점)
1. **교육적 적합성** (10점)
   - 학년 수준 적합도
   - 교육과정 연계성
   
2. **학습목표 부합** (10점)
   - 독해 능력 향상 기여도
   - 사고력 개발 효과

3. **난이도 일관성** (10점)
   - 표시된 난이도와 실제 일치
   - 단계적 학습 가능성

4. **피드백 품질** (10점)
   - 해설의 명확성
   - 오답 이유 설명

#### 기술적 측면 (30점)
5. **정답 명확성** (10점)
   - 정답의 객관성
   - 논란 여지 없음

6. **문제-지문 일치도** (10점)
   - 문제가 지문 내용 반영
   - 외부 지식 불필요

7. **문법 정확성** (10점)
   - 맞춤법, 띄어쓰기
   - 문장 구조 적절성

#### 창의적 측면 (30점)
8. **오답 매력도** (10점)
   - 그럴듯한 오답 구성
   - 실수 유도 적절성

9. **주제 관련성** (10점)
   - 현실성, 시의성
   - 학생 관심 유발

10. **창의성/참신성** (10점)
    - 독창적 접근
    - 다양한 사고 유도

### 4.2 Quality Thresholds
```
등급 분류:
├── S급 (90-100점): 즉시 사용 가능, 최우선 출제
├── A급 (80-89점): 우수 문제, 일반 출제 풀
├── B급 (70-79점): 사용 가능, 보조 문제
├── C급 (60-69점): 수정 필요, 검토 대상
└── D급 (60점 미만): 폐기 또는 전면 재작성
```

## 5. Random Quiz System

### 5.1 Quiz Generation Algorithm
```python
def generate_random_quiz(student_profile):
    """
    학생 맞춤형 랜덤 퀴즈 생성
    
    Parameters:
    - student_profile: 학생 수준, 학습 이력, 선호도
    
    Returns:
    - quiz: 10-20문제 세트
    """
    # 1. 학생 수준 분석
    level = analyze_student_level(student_profile)
    
    # 2. 이전 출제 기록 확인
    used_questions = get_student_history(student_profile.id)
    
    # 3. 적절한 난이도 분포
    difficulty_distribution = {
        'easy': 0.3 if level == 'beginner' else 0.2,
        'medium': 0.5 if level == 'intermediate' else 0.4,
        'hard': 0.2 if level == 'advanced' else 0.4
    }
    
    # 4. 중복 제외 랜덤 선택
    quiz = select_questions(
        exclude=used_questions,
        distribution=difficulty_distribution,
        count=calculate_quiz_length(student_profile)
    )
    
    return quiz
```

### 5.2 Adaptive Learning
- **초기 평가**: 실력 진단용 20문제
- **적응형 난이도**: 정답률에 따른 실시간 조정
- **학습 경로**: 개인별 최적 학습 순서 제공
- **재학습 추천**: 취약 영역 집중 훈련

## 6. Database Schema (Extended)

### 6.1 Core Tables

#### question_sets
```sql
CREATE TABLE question_sets (
    id UUID PRIMARY KEY,
    set_number INTEGER UNIQUE, -- 1-10
    name VARCHAR(100),
    description TEXT,
    total_questions INTEGER DEFAULT 100,
    created_at TIMESTAMP,
    status VARCHAR(50) -- 'generating', 'complete', 'validated'
);
```

#### questions_extended
```sql
CREATE TABLE questions_extended (
    id UUID PRIMARY KEY,
    set_id UUID REFERENCES question_sets(id),
    original_id VARCHAR(100), -- 기존 ID 체계 유지
    task_type VARCHAR(50),
    difficulty VARCHAR(20),
    topic VARCHAR(100),
    quality_score DECIMAL(5,2),
    quality_grade CHAR(1), -- 'S', 'A', 'B', 'C', 'D'
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2),
    avg_time_spent INTEGER, -- seconds
    content JSONB, -- 전체 문제 데이터
    created_at TIMESTAMP,
    validated_at TIMESTAMP
);
```

#### quality_evaluations
```sql
CREATE TABLE quality_evaluations (
    id UUID PRIMARY KEY,
    question_id UUID REFERENCES questions_extended(id),
    pedagogical_fitness INTEGER,
    learning_objective_match INTEGER,
    difficulty_consistency INTEGER,
    feedback_quality INTEGER,
    answer_clarity INTEGER,
    question_text_alignment INTEGER,
    grammar_correctness INTEGER,
    distractor_quality INTEGER,
    topic_relevance INTEGER,
    creativity_score INTEGER,
    total_score INTEGER,
    evaluator_type VARCHAR(50), -- 'auto', 'teacher', 'expert'
    evaluated_at TIMESTAMP,
    notes TEXT
);
```

#### random_quizzes
```sql
CREATE TABLE random_quizzes (
    id UUID PRIMARY KEY,
    student_id UUID REFERENCES users(id),
    quiz_date DATE,
    question_ids UUID[],
    difficulty_distribution JSONB,
    time_limit INTEGER,
    actual_time_spent INTEGER,
    score DECIMAL(5,2),
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP
);
```

## 7. API Endpoints (v2)

### 7.1 Generation APIs
```
POST   /api/v2/generate/batch     - 배치 생성 시작
GET    /api/v2/generate/status    - 생성 상태 확인
POST   /api/v2/generate/cancel    - 생성 취소
```

### 7.2 Quality APIs
```
POST   /api/v2/quality/evaluate   - 품질 평가 실행
GET    /api/v2/quality/report     - 평가 보고서
PUT    /api/v2/quality/override   - 수동 점수 조정
```

### 7.3 Quiz APIs
```
POST   /api/v2/quiz/generate      - 랜덤 퀴즈 생성
GET    /api/v2/quiz/{id}          - 퀴즈 조회
POST   /api/v2/quiz/submit        - 답안 제출
GET    /api/v2/quiz/history       - 퀴즈 이력
```

### 7.4 Analytics APIs
```
GET    /api/v2/analytics/student/{id}    - 학생 분석
GET    /api/v2/analytics/question/{id}   - 문제 분석
GET    /api/v2/analytics/class/{id}      - 반 전체 분석
POST   /api/v2/analytics/export          - 보고서 내보내기
```

## 8. Performance Requirements

### 8.1 Generation Performance
- **목표**: 시간당 100개 문제 생성
- **병렬 처리**: 3개 워커 동시 실행
- **재시도**: 실패 시 3회 자동 재시도
- **캐싱**: 자주 사용되는 프롬프트 캐싱

### 8.2 System Performance
- **API 응답**: < 200ms (캐시 히트)
- **퀴즈 생성**: < 500ms
- **품질 평가**: < 1초/문제
- **동시 사용자**: 1000명 이상

## 9. Implementation Timeline

### Week 1: Foundation
- Day 1-2: Architecture setup, parallel system
- Day 3-4: Upstage Solar Pro2 integration
- Day 5: Quality evaluation system

### Week 2: Scale Generation
- Day 6-7: Generate sets 3-6 (400 questions)
- Day 8-9: Generate sets 7-10 (400 questions)
- Day 10: Quality validation all 1000

### Week 3: Application Layer
- Day 11-12: Random quiz system
- Day 13-14: Student/Teacher portals
- Day 15: Integration testing

### Week 4: Polish & Deploy
- Day 16-17: Performance optimization
- Day 18-19: UI/UX refinement
- Day 20: Production deployment

## 10. Success Metrics

### 10.1 Quality Metrics
- **S+A급 비율**: > 50% (500+ questions)
- **사용 가능 비율**: > 70% (700+ questions)
- **평균 품질 점수**: > 75점

### 10.2 Educational Metrics
- **학습 효과**: 3개월 후 독해력 20% 향상
- **참여율**: 일일 활성 사용자 80% 이상
- **만족도**: 4.5/5.0 이상

### 10.3 Technical Metrics
- **생성 성공률**: > 95%
- **시스템 가동률**: > 99.9%
- **평균 응답 시간**: < 300ms

## 11. Risk Management

### 11.1 Quality Risks
- **Risk**: 품질 기준 미달 문제 과다
- **Mitigation**: 
  - 프롬프트 지속 개선
  - 수동 검토 프로세스
  - A/B 테스트

### 11.2 Technical Risks
- **Risk**: API 제한 또는 장애
- **Mitigation**:
  - 다중 API 키 로테이션
  - 로컬 백업 모델
  - 큐 시스템으로 재시도

### 11.3 Educational Risks
- **Risk**: 학생 수준과 불일치
- **Mitigation**:
  - 초기 진단 평가
  - 적응형 난이도 조정
  - 교사 피드백 반영

## 12. Future Enhancements

### Phase 2 (3-6 months)
- AI 튜터 기능 추가
- 음성 지원 (TTS/STR)
- 모바일 앱 개발
- 학부모 포털

### Phase 3 (6-12 months)
- 다국어 지원
- AR/VR 학습 경험
- 블록체인 인증서
- AI 생성 피드백 고도화

---

**Version**: 2.0
**Last Updated**: 2024-01-09
**Status**: In Development