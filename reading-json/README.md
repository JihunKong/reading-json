# 고2 사실적 읽기 JSON 파이프라인 (Local Docker)

이 레포는 **생산(Generator)** 과 **활용(Grader/활용도구)** 를 분리하여 운용합니다.
- Generator: 문단/글 + 문항 JSON을 **대량 생성**하고 검증/저장
- Grader: 학생 응답을 **채점/피드백**(오프라인 배치 또는 API 연동)

> 모든 작업은 로컬 Docker에서 수행하며, 외부 LLM 없이도 동작합니다.
> 필요 시 `.env`에서 임베딩/LLM API 키를 설정해 확장 가능합니다.

## 구조
```
.
├─ generator/                 # 생산 파이프라인 (생성기)
│  ├─ README.md
│  ├─ prompts/               # 생성 프롬프트 템플릿(.md)
│  ├─ schemas/               # JSON 스키마 및 예제
│  ├─ seeds/                 # 주제 시드 CSV/JSON
│  ├─ out/                   # 생성 결과(JSON) 기본 출력 폴더
│  └─ Dockerfile
├─ grader/                    # 활용 파이프라인 (채점기)
│  ├─ README.md
│  ├─ schemas/               # 동일 스키마 참조(하위셋)
│  ├─ samples/               # 샘플 학생 응답
│  ├─ reports/               # 채점/리포트 산출물
│  └─ Dockerfile
├─ DATAFLOW.md                # 데이터 흐름/운영 시나리오
├─ SCHEMA.md                  # 공통 JSON 스키마 명세
├─ PROMPTS.md                 # 프롬프트 설계 가이드
├─ .env.example               # 환경 변수 예시
├─ docker-compose.yml         # 로컬 멀티 컨테이너 오케스트레이션
└─ Makefile                   # 자주 쓰는 명령 모음
```

## 빠른 시작
```bash
cp .env.example .env
docker compose build
docker compose run --rm generator generate --count 5 --mode paragraph
docker compose run --rm grader grade-sample --input grader/samples/submissions.csv
```
