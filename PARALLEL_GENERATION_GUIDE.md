# 한국어 독해 문제 1000개 병렬 생성 시스템

한국어 독해 문제 생성을 위한 고성능 병렬 처리 시스템입니다. Upstage Solar Pro2 API를 활용하여 3개 워커 프로세스가 동시에 작업하며, 실시간 품질 검증과 진행 상황 모니터링을 제공합니다.

## 🚀 주요 기능

- **3개 워커 프로세스 동시 실행**: multiprocessing과 asyncio를 활용한 병렬 처리
- **Upstage Solar Pro2 API**: 한국어에 최적화된 LLM 활용
- **실패 자동 재시도**: 최대 3회까지 자동 재시도
- **실시간 진행 상황 모니터링**: Rich UI를 통한 시각적 모니터링
- **세트별 구조화 저장**: 100개씩 세트로 나누어 체계적 저장
- **실시간 품질 검증**: 생성과 동시에 품질 평가 및 개선 제안

## 📁 파일 구조

```
generator/
├── parallel_generator.py     # 메인 병렬 생성 엔진
├── upstage_client.py        # Upstage API 클라이언트
├── quality_validator.py     # 실시간 품질 검증기
├── progress_monitor.py      # 진행 상황 모니터링
├── requirements_parallel.txt # 의존성 패키지
└── parallel_sets/           # 생성 결과 (자동 생성)
    ├── set_1/
    │   ├── paragraphs/      # 문단 과제
    │   ├── articles/        # 글 과제
    │   └── reports/         # 세트 보고서
    ├── set_2/
    └── ...
```

## 🛠️ 설치 및 설정

### 1. 환경 설정

```bash
# 의존성 패키지 설치
cd generator
pip install -r requirements_parallel.txt

# 선택적: Rich UI를 위한 추가 패키지
pip install rich
```

### 2. API 키 설정

`.env` 파일에서 실제 Upstage API 키로 변경:

```bash
# .env 파일 편집
UPSTAGE_API_KEY=실제_업스테이지_API_키_입력
```

**중요**: `up_xxxxxxxxxxxxxxxxxxxx`를 실제 API 키로 교체해주세요.

## 🚀 실행 방법

### 기본 실행 (1000개 생성)

```bash
cd generator
python parallel_generator.py
```

### 사용자 정의 설정

```bash
# 100개만 생성 (테스트용)
python parallel_generator.py --total 100

# 5개 워커로 실행
python parallel_generator.py --workers 5

# 배치 크기 조정
python parallel_generator.py --batch-size 20

# 출력 디렉토리 지정
python parallel_generator.py --output-dir my_questions

# 모든 옵션 조합
python parallel_generator.py --total 500 --workers 4 --batch-size 15 --output-dir test_output
```

### 명령줄 옵션

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--total` | 1000 | 총 생성할 작업 수 |
| `--workers` | 3 | 워커 프로세스 수 |
| `--batch-size` | 10 | 배치 크기 |
| `--output-dir` | "parallel_sets" | 출력 디렉토리 |

## 📊 실시간 모니터링

실행 중 다음과 같은 정보가 실시간으로 표시됩니다:

### Rich UI 모드 (권장)
- 📈 생성 통계: 진행률, 성공률, 처리량
- 👷 워커 상태: 각 워커의 현재 작업 상태
- 📋 실시간 로그: 최근 이벤트 및 오류

### 간단 모드 (Rich 없음)
- 텍스트 기반 진행률 표시
- 기본 통계 정보

## 📁 출력 구조

생성된 결과는 다음과 같이 구조화되어 저장됩니다:

```
parallel_sets/
├── set_1/ (첫 번째 100개)
│   ├── paragraphs/
│   │   ├── para_1234567890_0001.json
│   │   └── ...
│   ├── articles/
│   │   ├── art_1234567890_0061.json
│   │   └── ...
│   └── reports/
│       ├── set_summary.json
│       └── set_summary.txt
├── set_2/ (두 번째 100개)
└── final_report.json (전체 요약)
```

### 개별 과제 파일 구조

```json
{
  "id": "para_1234567890_0001",
  "task_type": "paragraph",
  "topic": "인공지능의 발전과 사회 변화",
  "difficulty": "medium",
  "content": "문단 내용...",
  "q_keywords_mcq": { ... },
  "q_center_sentence_mcq": { ... },
  "q_topic_free": { ... },
  "validation": {
    "is_valid": true,
    "confidence": 0.85,
    "overall_score": 78.5,
    "issues_count": 2,
    "strengths_count": 4
  }
}
```

## 📈 성능 특징

### 처리 속도
- **3개 워커**: 약 2-3작업/초 (네트워크 상태에 따라 변동)
- **1000개 완성**: 약 15-20분 소요 (예상)

### 품질 관리
- **실시간 검증**: 생성과 동시에 품질 평가
- **자동 재시도**: 실패 시 최대 3회 재시도
- **구조 검증**: JSON 형식 및 필수 필드 확인
- **내용 검증**: 교육적 가치 및 적절성 평가

## 🔧 고급 사용법

### 테스트 실행

소규모 테스트부터 시작하는 것을 권장합니다:

```bash
# 10개만 생성해서 테스트
python parallel_generator.py --total 10

# API 키가 올바른지 확인
python upstage_client.py  # 테스트 실행

# 품질 검증기 테스트
python quality_validator.py  # 검증기 테스트
```

### 중단 및 재시작

- **중단**: `Ctrl+C`로 안전하게 중단 가능
- **재시작**: 새로운 세트로 시작 (기존 파일 보존)
- **부분 실행**: `--total` 옵션으로 필요한 만큼만 생성

### 로그 확인

```bash
# 실행 로그 확인
tail -f parallel_generation.log

# 품질 이슈 분석
grep "validation" parallel_generation.log
```

## 🎯 작업 분포

기본 설정으로 다음 비율로 생성됩니다:

- **문단 과제**: 60% (600개)
  - 3-5문장 구성
  - 핵심어, 중심문장, 주제 문제

- **글 과제**: 40% (400개)
  - 3-4문단 구성
  - 핵심어, 중심문단, 주제 문제

## 📋 주제 카테고리

총 75개 고등학교 교육과정 기반 주제:

- 🔬 **과학기술**: AI, 스마트시티, 재생에너지 등
- 🌱 **환경생태**: 기후변화, 생물다양성, 지속가능성 등
- 🏛️ **사회문화**: 다문화, 세대소통, 글로벌 시민의식 등
- 💼 **경제진로**: 창업, 디지털경제, 평생학습 등
- 💚 **건강안전**: 정신건강, 사이버보안, 재난대비 등
- 🗳️ **민주인권**: 시민참여, 인권존중, 사회정의 등
- 📚 **교육학습**: 독서, 창의적사고, 협동학습 등

## 📊 품질 지표

각 과제는 다음 기준으로 평가됩니다:

- **구조 완성도**: JSON 형식, 필수 필드
- **내용 품질**: 길이, 일관성, 주제 관련성
- **문제 적절성**: 선택지, 정답, 설명의 타당성
- **교육적 가치**: 고등학교 수준 적합성

**목표 품질**:
- 검증 통과율: 80% 이상
- 평균 품질 점수: 75점 이상
- 평균 신뢰도: 0.7 이상

## ⚠️ 주의사항

1. **API 키**: 반드시 실제 Upstage API 키 설정 필요
2. **네트워크**: 안정적인 인터넷 연결 필요
3. **메모리**: 대용량 생성 시 충분한 메모리 필요
4. **디스크 공간**: 1000개 기준 약 10-20MB 소요

## 🔧 문제 해결

### 일반적인 문제

**Q: "UPSTAGE_API_KEY가 설정되지 않았습니다" 오류**
A: `.env` 파일에서 `UPSTAGE_API_KEY=실제키`로 설정

**Q: Rich UI가 표시되지 않음**
A: `pip install rich` 실행 후 재시도

**Q: 워커가 멈춤**
A: API 키 확인, 네트워크 상태 점검

**Q: 생성 품질이 낮음**
A: `quality_validator.py` 기준 조정 검토

### 성능 최적화

- **워커 수 증가**: `--workers 5` (API 한도 고려)
- **배치 크기 조정**: `--batch-size 20` (메모리 사용량 고려)
- **네트워크 최적화**: 안정적인 연결 환경 확보

## 📞 지원

문제가 발생하거나 개선 사항이 있으면:

1. 로그 파일 확인: `parallel_generation.log`
2. 테스트 실행: `python upstage_client.py`
3. 개별 컴포넌트 테스트 실행

---

**⚡ 고성능 병렬 생성으로 효율적인 한국어 독해 문제 제작을 경험해보세요!**