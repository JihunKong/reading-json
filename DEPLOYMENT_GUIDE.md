# 한국어 독해 학습 시스템 배포 가이드

## 📋 시스템 개요

고등학교 2학년 대상 한국어 독해 학습 시스템으로, 100개의 검증된 학습 자료와 실시간 분석 기능을 제공합니다.

## 🔧 기술 스택

- **Backend**: FastAPI + Uvicorn
- **Database**: PostgreSQL 14+ with pgvector
- **Authentication**: Google OAuth 2.0
- **Cache**: Redis
- **Storage**: AWS S3 (선택사항)
- **Container**: Docker
- **Orchestration**: Kubernetes (선택사항)

## 📦 설치 요구사항

### 1. 시스템 요구사항
```bash
- Python 3.9+
- PostgreSQL 14+
- Redis 6+
- Node.js 16+ (프론트엔드용)
```

### 2. Python 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정
`.env` 파일 생성:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/reading_db
REDIS_URL=redis://localhost:6379

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# AWS S3 (선택사항)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_BUCKET_NAME=reading-system-bucket
AWS_REGION=ap-northeast-2

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
```

## 🗄️ 데이터베이스 설정

### 1. PostgreSQL 설치 및 설정
```bash
# PostgreSQL 설치 (macOS)
brew install postgresql@14
brew services start postgresql@14

# 데이터베이스 생성
createdb reading_db

# pgvector 확장 설치
brew install pgvector
```

### 2. 스키마 적용
```bash
psql -d reading_db -f database_schema.sql
```

### 3. 초기 데이터 로드
```bash
python scripts/load_initial_data.py
```

## 🔐 Google OAuth 설정

### 1. Google Cloud Console 설정
1. [Google Cloud Console](https://console.cloud.google.com) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. "APIs & Services" → "Credentials" 이동
4. "Create Credentials" → "OAuth client ID" 선택
5. Application type: "Web application" 선택
6. Authorized redirect URIs 추가:
   - 개발: `http://localhost:8000/auth/callback`
   - 프로덕션: `https://yourdomain.com/auth/callback`

### 2. OAuth 동의 화면 구성
1. "OAuth consent screen" 탭 선택
2. User Type: "External" 선택
3. 앱 정보 입력:
   - App name: "한국어 독해 학습 시스템"
   - User support email: 지원 이메일
   - Developer contact: 개발자 이메일
4. Scopes 추가:
   - `openid`
   - `email`
   - `profile`

## 🐳 Docker 배포

### 1. Docker 이미지 빌드
```bash
docker build -t reading-system:latest .
```

### 2. Docker Compose 실행
```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: reading_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database_schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
    ports:
      - "5432:5432"

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/reading_db
      REDIS_URL: redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./generator/batch_out_2024:/app/data

volumes:
  postgres_data:
```

### 3. 실행
```bash
docker-compose up -d
```

## 🚀 프로덕션 배포

### 1. Gunicorn 설정
```python
# gunicorn_config.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True
accesslog = "-"
errorlog = "-"
```

### 2. Nginx 설정
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 3. SSL 설정 (Let's Encrypt)
```bash
sudo certbot --nginx -d yourdomain.com
```

### 4. Systemd 서비스
```ini
# /etc/systemd/system/reading-system.service
[Unit]
Description=Korean Reading Comprehension System
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/reading-system
Environment="PATH=/opt/reading-system/venv/bin"
ExecStart=/opt/reading-system/venv/bin/gunicorn -c gunicorn_config.py api_endpoints:app

[Install]
WantedBy=multi-user.target
```

## 📊 모니터링

### 1. Prometheus 설정
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'reading-system'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### 2. Grafana 대시보드
- API 응답 시간
- 활성 사용자 수
- 학습 완료율
- 시스템 리소스 사용량

## 🔄 백업 및 복구

### 1. 데이터베이스 백업
```bash
# 백업
pg_dump reading_db > backup_$(date +%Y%m%d).sql

# 복구
psql reading_db < backup_20240109.sql
```

### 2. 자동 백업 설정 (cron)
```bash
# crontab -e
0 2 * * * pg_dump reading_db > /backups/reading_db_$(date +\%Y\%m\%d).sql
```

## 🧪 테스트

### 1. 단위 테스트
```bash
pytest tests/unit/
```

### 2. 통합 테스트
```bash
pytest tests/integration/
```

### 3. 부하 테스트
```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

## 📱 클라이언트 연동

### 1. API 문서 확인
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 2. WebSocket 연결
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('실시간 업데이트:', data);
};
```

## 🛠️ 유지보수

### 1. 로그 확인
```bash
# API 로그
tail -f /var/log/reading-system/api.log

# 데이터베이스 로그
tail -f /var/log/postgresql/postgresql-14-main.log
```

### 2. 성능 최적화
- 데이터베이스 인덱스 정기 재구성
- Redis 캐시 TTL 조정
- API 응답 시간 모니터링

### 3. 보안 업데이트
```bash
# 정기적인 패키지 업데이트
pip list --outdated
pip install --upgrade [package]

# SSL 인증서 갱신
certbot renew
```

## 📞 지원

문제 발생 시:
1. 로그 파일 확인
2. [GitHub Issues](https://github.com/yourusername/reading-system/issues) 확인
3. 개발팀 연락

## 📝 라이센스

MIT License - 자유롭게 사용 및 수정 가능합니다.

---

**버전**: 1.0.0  
**최종 업데이트**: 2025-09-09