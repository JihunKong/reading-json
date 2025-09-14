# 🐳 한국어 학습 시스템 Docker 배포 가이드

온라인 도커 시스템 및 로컬 환경에서의 완전한 배포 가이드입니다.

## 🎯 시스템 개요

이 시스템은 다음과 같은 교육 기능을 제공합니다:

- **4단계 한국어 요약 학습**: 성분식별 → 필요성판단 → 일반화 → 주제재구성
- **실시간 교사 대시보드**: 학생 진행 상황 모니터링 및 개입
- **한국어 NLP**: KoNLPy 기반 문법 분석 및 텍스트 처리
- **웹소켓 실시간 통신**: 교사-학생 간 실시간 상호작용

## 🚀 빠른 시작

### 1단계: 사전 요구사항

```bash
# Docker 및 Docker Compose 설치 확인
docker --version
docker-compose --version

# 필요 시 Docker 설치 (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Docker Compose 설치
sudo apt-get install docker-compose-plugin
```

### 2단계: 프로젝트 클론 및 설정

```bash
# 프로젝트 디렉토리로 이동
cd /Users/jihunkong/reading-json

# 환경 설정 파일 복사
cp .env.docker .env

# 필요 시 환경 변수 수정
nano .env
```

### 3단계: 한 번의 명령으로 실행

```bash
# 전체 시스템 빌드 및 시작
./deploy.sh start

# 또는 Docker Compose 직접 사용
docker-compose up --build -d
```

### 4단계: 접속 확인

```bash
# 웹 브라우저에서 접속
open http://localhost:8080

# 상태 확인
./deploy.sh status
```

## 🛠️ 상세 배포 가이드

### 로컬 개발 환경

```bash
# 개발 모드로 실행 (실시간 코드 변경 반영)
FLASK_ENV=development docker-compose up

# 개발용 포트에서 실행
docker-compose -f docker-compose.dev.yml up
```

### 프로덕션 환경

```bash
# 프로덕션 이미지 빌드
docker-compose -f docker-compose.prod.yml build

# 백그라운드에서 실행
docker-compose -f docker-compose.prod.yml up -d

# 로드 밸런싱을 위한 스케일링
docker-compose up --scale korean-learning-system=3
```

## 📊 서비스 구성

| 서비스 | 포트 | 설명 |
|--------|------|------|
| korean-learning-system | 8080 | 메인 Flask 애플리케이션 |
| redis | 6379 | 캐시 및 세션 저장소 |

## 🔧 배포 스크립트 사용법

`deploy.sh` 스크립트는 시스템 관리를 위한 모든 기능을 제공합니다:

```bash
# 시스템 시작
./deploy.sh start

# 시스템 중지
./deploy.sh stop

# 시스템 재시작
./deploy.sh restart

# 실시간 로그 확인
./deploy.sh logs

# 시스템 상태 확인
./deploy.sh status

# 전체 재배포
./deploy.sh redeploy

# 도움말
./deploy.sh help
```

## 🌐 온라인 Docker 플랫폼 배포

### Docker Hub 배포

```bash
# 이미지 빌드 및 태그
docker build -t your-username/korean-learning-system:latest .

# Docker Hub에 푸시
docker push your-username/korean-learning-system:latest

# 원격에서 실행
docker run -d -p 8080:8080 your-username/korean-learning-system:latest
```

### AWS ECS 배포

```bash
# AWS CLI 설정 후
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# ECR에 이미지 푸시
docker build -t korean-learning-system .
docker tag korean-learning-system:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/korean-learning-system:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/korean-learning-system:latest
```

### Kubernetes 배포

```yaml
# k8s-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: korean-learning-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: korean-learning-system
  template:
    metadata:
      labels:
        app: korean-learning-system
    spec:
      containers:
      - name: korean-learning-system
        image: your-username/korean-learning-system:latest
        ports:
        - containerPort: 8080
        env:
        - name: LANG
          value: "ko_KR.UTF-8"
```

## 🗄️ 데이터 영속성

### 볼륨 설정

```yaml
volumes:
  # 학습 데이터 영속성
  - ./data:/app/data
  # 로그 파일 영속성  
  - ./logs:/app/logs
  # Redis 데이터 영속성
  - redis_data:/data
```

### 백업 및 복원

```bash
# 데이터 백업
docker exec korean-learning-app tar -czf - /app/data | cat > backup.tar.gz

# 데이터 복원
cat backup.tar.gz | docker exec -i korean-learning-app tar -xzf - -C /
```

## 🔍 모니터링 및 로그

### 실시간 로그 모니터링

```bash
# 전체 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f korean-learning-system

# 에러 로그만 필터링
docker-compose logs korean-learning-system | grep ERROR
```

### 헬스체크

```bash
# 헬스체크 상태 확인
curl http://localhost:8080/api/status

# 자세한 상태 정보
curl http://localhost:8080/api/health
```

## ⚡ 성능 최적화

### 메모리 및 CPU 제한

```yaml
services:
  korean-learning-system:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
```

### Redis 최적화

```yaml
redis:
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

## 🔒 보안 설정

### 환경 변수 보안

```bash
# 프로덕션 환경에서는 반드시 변경
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=production
DEBUG=false
```

### 네트워크 보안

```yaml
networks:
  korean-learning-network:
    driver: bridge
    driver_opts:
      encrypted: "true"
```

## 🚨 문제 해결

### 일반적인 문제

**1. 포트 충돌**
```bash
# 포트 사용 확인
lsof -i :8080
# 다른 포트로 실행
PORT=8081 docker-compose up
```

**2. 메모리 부족**
```bash
# 메모리 사용량 확인
docker stats
# 사용하지 않는 이미지 정리
docker system prune -a
```

**3. 한국어 폰트 문제**
```bash
# 컨테이너 내부에서 폰트 확인
docker exec -it korean-learning-app fc-list | grep -i nanum
```

### 로그 분석

```bash
# 시스템 시작 오류
docker-compose logs korean-learning-system | grep "Error\\|Exception"

# 한국어 NLP 초기화 확인
docker-compose logs korean-learning-system | grep "Korean analyzer"

# 웹소켓 연결 확인
docker-compose logs korean-learning-system | grep "SocketIO"
```

## 📋 체크리스트

### 배포 전 확인사항
- [ ] Docker 및 Docker Compose 설치 확인
- [ ] 환경 변수 설정 (.env 파일)
- [ ] 포트 8080 사용 가능 확인
- [ ] 충분한 디스크 공간 (최소 5GB)

### 배포 후 확인사항
- [ ] 웹 페이지 정상 접속 (http://localhost:8080)
- [ ] 4단계 학습 시스템 작동 확인
- [ ] 교사 대시보드 접속 확인
- [ ] 웹소켓 실시간 통신 확인
- [ ] 한국어 텍스트 정상 표시 확인

## 🆘 지원 및 도움

### 문서
- [Flask 공식 문서](https://flask.palletsprojects.com/)
- [KoNLPy 가이드](https://konlpy.org/)
- [Docker Compose 문서](https://docs.docker.com/compose/)

### 커뮤니티
- GitHub Issues: 버그 리포트 및 기능 요청
- Discord: 실시간 지원 및 커뮤니티
- 이메일: technical-support@korean-learning.edu

---

**🎓 실제 교실에서 즉시 사용 가능한 한국어 학습 시스템**

이 시스템은 실제 교육 현장에서 검증된 4단계 요약 학습 방법론을 바탕으로 개발되었습니다. Docker를 통해 어디서든 쉽게 배포하고 사용할 수 있습니다.