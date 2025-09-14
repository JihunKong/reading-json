# PRD: Korean Reading Comprehension System

## 1. Product Overview

### Vision
고등학생을 위한 한국어 독해 능력 평가 및 학습 시스템으로, 교육적으로 유의미한 질 높은 문제를 생성하고 즉시 피드백을 제공합니다.

### Mission
- 정확하고 교육적으로 적합한 독해 문제 생성
- 학생의 독해 능력을 정확히 측정
- 즉시적이고 건설적인 피드백 제공

## 2. Current System Analysis

### 2.1 Architecture Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Generator     │    │   Web Interface │    │     Grader      │
│                 │    │                 │    │                 │
│ - LLM Content   │───▶│ - Flask Server  │───▶│ - Auto Scoring  │
│ - JSON Schema   │    │ - SocketIO      │    │ - Similarity    │
│ - Validation    │    │ - Question UI   │    │ - Reports       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 2.2 Current Features
#### Generator
- **Content Types**: 문단(paragraph), 글(article)
- **Question Types**: 
  - 핵심어 파악 (4지선다)
  - 중심문장/중심문단 파악 (5지선다)
  - 주제 서술 (자유응답)
- **Topics**: 44개 주제 (교육, 환경, 기술, 사회, 건강)
- **Difficulty**: easy, medium, hard

#### Web Interface
- 실시간 문제 제시
- 단계별 질문 진행
- 즉시 채점 및 피드백
- 반응형 UI

#### Grader
- 다지선다 자동채점
- 자유응답 유사도 분석 (cosine similarity)
- 품사 검증 (명사, 동사 포함 확인)
- CSV 리포트 생성

## 3. Critical Issues Identified

### 3.1 🚨 PRIMARY ISSUE: 부적절한 정답 선택
**문제**: LLM이 생성한 핵심어 문제에서 정답이 지문의 주제와 일치하지 않음

**실제 사례**:
```json
{
  "paragraph": {
    "text": "인공지능 교육은 미래 사회를 대비하는 필수 과정이다...",
    "topic_hint": "스마트시티"
  },
  "q_keywords_mcq": {
    "choices": ["인공지능 교육", "미래", "프로그래밍", "학생"],
    "answer_index": 0,  // "인공지능 교육"이 정답이어야 함
    "rationale": "문단의 중심 개념을 나타내는 핵심어가 정답입니다."
  }
}
```

**실제 발생한 오류 사례**:
- 지문: AI 교육에 관한 내용
- 정답으로 선택됨: "머신러닝" (선택지에도 없었을 가능성)
- 올바른 정답: "AI 교육" 또는 "인공지능 교육"

### 3.2 중심문장 식별 논리 오류
**문제**: 첫 번째 문장이 명확한 주제문임에도 불구하고 다른 문장을 중심문장으로 선택

### 3.3 Topic Hint vs 실제 내용 불일치
**문제**: `topic_hint`가 "스마트시티"인데 실제 지문은 "AI 교육"에 관한 내용

## 4. Technical Requirements

### 4.1 Content Generation Quality Standards
#### 핵심어 문제 기준
1. **정답 검증**: 핵심어는 반드시 지문의 주요 주제여야 함
2. **선택지 품질**: 4개 선택지 모두 지문에서 언급되는 단어여야 함
3. **오답 매력도**: 오답도 지문과 관련있지만 주제가 아닌 세부사항이어야 함

#### 중심문장 문제 기준
1. **논리적 식별**: 문단의 주제를 포괄하는 문장 선택
2. **구조 이해**: 도입-본론-결론 구조 고려
3. **교육적 가치**: 학생이 올바른 독해 전략을 학습할 수 있어야 함

### 4.2 Data Consistency Requirements
1. **Topic Alignment**: `topic_hint`와 실제 지문 내용 일치
2. **Schema Validation**: 모든 필수 필드 존재 확인
3. **Answer Validation**: 정답이 실제로 선택지에 존재하는지 확인

## 5. User Experience Requirements

### 5.1 Student Interface
- 명확하고 직관적인 문제 제시
- 단계별 진행 상황 표시
- 즉시 피드백 제공
- 오답에 대한 설명 제공

### 5.2 Teacher Interface (Future)
- 문제 품질 검토 도구
- 학생 성과 분석
- 커스텀 문제 생성

## 6. Success Metrics

### 6.1 Quality Metrics
- **Answer Accuracy**: 생성된 정답의 교육적 적절성 > 95%
- **Content Relevance**: 지문과 질문의 일치도 > 98%
- **Schema Compliance**: JSON 스키마 준수율 100%

### 6.2 Educational Metrics
- **Learning Effectiveness**: 학생의 독해 능력 향상 측정
- **Engagement**: 문제 완료율 > 85%
- **Satisfaction**: 학생/교사 만족도 > 4.0/5.0

## 7. Implementation Roadmap

### Phase 1: Quality Assurance (우선순위 최고)
1. **Answer Validation Logic**
   - 핵심어 정답 검증 알고리즘 구현
   - 중심문장 식별 논리 개선
   - Topic-content alignment 검증

2. **Content Review System**
   - 생성된 문제의 품질 검토 도구
   - 부적절한 문제 필터링
   - 수동 검토 워크플로

### Phase 2: Enhanced Generation
1. **Improved LLM Prompting**
   - 더 정확한 프롬프트 엔지니어링
   - Few-shot learning examples
   - 검증 단계 추가

2. **Multi-step Validation**
   - 생성 → 검증 → 수정 → 재검증 파이프라인
   - 교육 전문가 검토 단계

### Phase 3: Advanced Features
1. **Adaptive Difficulty**
   - 학생 수준에 맞는 난이도 조정
   - 개인화된 문제 추천

2. **Analytics Dashboard**
   - 실시간 성과 모니터링
   - 문제 품질 지표 추적

## 8. Risk Mitigation

### 8.1 Content Quality Risks
- **Risk**: 교육적으로 부적절한 문제 생성
- **Mitigation**: 다단계 검증 시스템, 전문가 검토

### 8.2 Technical Risks
- **Risk**: 시스템 장애로 인한 학습 중단
- **Mitigation**: 견고한 에러 핸들링, 백업 시스템

## 9. Immediate Action Items

### 🔥 Critical (즉시 수정 필요)
1. **Answer Selection Algorithm**: 핵심어 정답 선택 논리 완전 재작성
2. **Content Validation**: 생성된 모든 문제에 대한 품질 검증 도구 개발
3. **Topic Consistency**: topic_hint와 실제 내용 일치성 확보

### 📊 High Priority
1. **Center Sentence Logic**: 중심문장 식별 알고리즘 개선
2. **Schema Enforcement**: 필수 필드 검증 강화
3. **Error Handling**: 웹 인터페이스 오류 처리 개선

### 📈 Medium Priority
1. **Performance Optimization**: 대량 문제 생성 최적화
2. **UI/UX Enhancement**: 사용자 경험 개선
3. **Reporting System**: 상세한 분석 리포트 기능

## 10. Conclusion

현재 시스템은 기술적 기반은 견고하지만, **교육적 품질**에서 심각한 문제를 보이고 있습니다. 특히 "정답이 없는 문제"를 생성하는 것은 교육 시스템으로서 치명적인 결함입니다.

**최우선 과제**는 LLM 생성 논리를 근본적으로 개선하여 교육적으로 의미있고 정확한 문제만을 생성하도록 하는 것입니다.