# Vercel 배포 가이드

## 🚀 Vercel 배포 준비

이 프로젝트를 Vercel에 배포하기 위한 설정 가이드입니다.

## 📋 필요한 파일들

### 1. `vercel.json` - Vercel 설정 파일 ✅
```json
{
  "version": 2,
  "builds": [
    {
      "src": "web_app.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "15mb"
      }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "web_app.py"
    }
  ],
  "env": {
    "FLASK_ENV": "production",
    "FLASK_DEBUG": "false"
  }
}
```

### 2. `requirements.txt` - Python 패키지 목록 ✅
Vercel 배포를 위한 최소한의 패키지만 포함:
```
Flask==3.0.0
requests==2.31.0
```

**주의**: 무거운 패키지들(pandas, numpy, konlpy 등)은 Vercel의 빌드 제한으로 인해 제외됨

### 3. `.gitignore` - Git 무시 파일 ✅
환경변수, 로그, 캐시 파일들을 Git에서 제외합니다.

## 🔧 Vercel 환경변수 설정

Vercel 대시보드에서 다음 환경변수들을 설정해야 합니다:

### 필수 환경변수

이 프로젝트는 AI 기반 문제 생성을 위해 Upstage API를 사용합니다. Vercel 대시보드에서 다음 환경변수들을 **반드시** 설정해야 합니다:

```bash
# Upstage API (필수) - 한국어 최적화 LLM
UPSTAGE_API_KEY=up_xxxxxxxxxxxxxxxxxxxxxxxx
UPSTAGE_BASE_URL=https://api.upstage.ai/v1
UPSTAGE_MODEL=solar-pro2
UPSTAGE_EMBEDDING_MODEL=embedding-query

# Flask 설정 (필수)
FLASK_ENV=production
FLASK_DEBUG=false
```

### 선택적 환경변수

추가 기능을 위해 다음 환경변수들을 설정할 수 있습니다:

```bash
# 로깅 레벨
LOG_LEVEL=INFO

# 애플리케이션 설정
APP_SECRET_KEY=your-secret-key-here

# 데이터베이스 (향후 사용시)
DATABASE_URL=your-database-url

# 다른 AI API Keys (선택적)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

### 🔑 Upstage API 키 발급 받기

1. [Upstage Console](https://console.upstage.ai/) 접속
2. 회원가입 및 로그인
3. API 키 생성
4. 생성된 키를 Vercel 환경변수로 설정

## 📦 배포 단계

### 1. GitHub 저장소 연결
1. [Vercel 대시보드](https://vercel.com/dashboard)에 로그인
2. "New Project" 클릭
3. GitHub 저장소 `JihunKong/reading-json` 선택
4. "Import" 클릭

### 2. 프로젝트 설정
1. **Framework Preset**: Other 선택
2. **Root Directory**: `/` (기본값)
3. **Build Command**: 기본값 사용 (비어두기)
4. **Output Directory**: 기본값 사용 (비어두기)
5. **Install Command**: `pip install -r requirements.txt`

### 3. 환경변수 설정 (선택적)
1. "Environment Variables" 섹션에서 필요한 변수들 추가
2. Production, Preview, Development 환경별로 설정 가능

### 4. 배포 실행
1. "Deploy" 버튼 클릭
2. 배포 완료까지 2-3분 대기

## 🌐 배포 후 확인사항

### 1. 기본 기능 테스트
- [ ] 메인 페이지 로딩 확인
- [ ] 학습 문제 생성 테스트
- [ ] 답안 제출 및 채점 기능 확인
- [ ] 새 문제 생성 기능 확인

### 2. 성능 확인
- [ ] 페이지 로딩 속도 (3초 이내)
- [ ] API 응답 시간 확인
- [ ] 모바일 반응형 확인

## 🔍 문제 해결

### 배포 실패시
1. **Python 버전 문제**: `runtime.txt` 파일로 Python 버전 지정
2. **패키지 설치 실패**:
   - `JPype1`, `numpy`, `pandas` 등 컴파일 필요한 패키지 제거
   - Vercel은 순수 Python 패키지만 지원
   - `requirements.txt`를 Flask와 requests만으로 최소화
3. **메모리 초과**: Vercel의 512MB 제한 확인
4. **distutils 오류**: Python 3.12 호환성 문제로 인한 빌드 실패
   - 최소한의 패키지만 사용하여 해결

### 런타임 오류시
1. **템플릿 파일 없음**: `templates/` 디렉토리 확인
2. **정적 파일 404**: `static/` 디렉토리 경로 확인
3. **함수 타임아웃**: `vercel.json`의 `maxDuration` 조정

## 📱 도메인 설정

### 1. 커스텀 도메인 (선택적)
1. Vercel 프로젝트 설정 → Domains
2. 도메인 추가 및 DNS 설정
3. SSL 인증서 자동 발급 확인

### 2. 기본 Vercel 도메인
배포 완료 후 `https://your-project-name.vercel.app` 형태의 URL 제공

## 🔄 지속적 배포

GitHub에 push할 때마다 Vercel이 자동으로:
1. 새 버전 빌드
2. 테스트 환경에 배포 (Preview)
3. main 브랜치는 Production에 자동 배포

## 📊 모니터링

Vercel 대시보드에서 확인 가능한 지표:
- 배포 상태 및 로그
- 함수 실행 시간
- 트래픽 및 대역폭 사용량
- 오류 발생 현황

---

## 🚨 주의사항

1. **무료 계획 제한**:
   - 월 100GB 대역폭
   - 함수 실행 시간 10초 (Hobby 플랜)
   - 동시 함수 실행 수 제한

2. **보안**:
   - 환경변수에 민감한 정보 저장
   - `.env` 파일은 Git에 커밋하지 않기

3. **성능**:
   - 첫 번째 요청시 Cold Start 지연 가능
   - 정적 파일은 CDN을 통해 빠른 로딩

이제 `git add .` → `git commit` → `git push` 후 Vercel에서 배포하시면 됩니다! 🎉