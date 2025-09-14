# Korean Learning System - Docker Deployment Guide

Complete Docker deployment environment for the Korean Reading Comprehension Learning System, supporting both local development and production deployment across multiple platforms.

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+ with BuildKit support
- Docker Compose v2.0+
- 4GB+ RAM available
- 10GB+ disk space

### Basic Deployment

```bash
# 1. Copy environment configuration
cp .env.docker .env

# 2. Build and start the system
./build.sh
./run.sh up --detach

# 3. Verify deployment
./run.sh test

# 4. Access the application
open http://localhost:8080
```

## 📁 File Structure

```
korean-learning-system/
├── Dockerfile.flask              # Main Flask application container
├── docker-compose-complete.yml   # Complete deployment configuration
├── .env.docker                   # Docker environment variables
├── .dockerignore                 # Optimized build context
├── build.sh                      # Build script
├── run.sh                        # Run and management script
├── deploy.sh                     # Production deployment script
├── nginx/                        # Nginx reverse proxy configuration
│   ├── nginx.conf
│   └── conf.d/korean-learning.conf
├── app/                          # Flask application code
├── core/                         # Korean NLP processing modules
├── data/                         # Persistent data storage
└── generator/                    # Content generation tools
```

## 🛠 Configuration

### Environment Variables

The system uses `.env.docker` for configuration. Key variables:

```bash
# Application
FLASK_PORT=8080
BUILD_TARGET=production
SECRET_KEY=your-secret-key

# Database
DB_NAME=korean_learning
DB_USER=korean_user
DB_PASSWORD=secure_password

# Korean NLP
KONLPY_BACKEND=mecab
DEFAULT_SIMILARITY_THRESHOLD=0.68

# API Keys (Optional)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
UPSTAGE_API_KEY=your-upstage-key
```

### Service Ports

- **8080**: Main Flask application
- **5432**: PostgreSQL database
- **6379**: Redis cache
- **80/443**: Nginx reverse proxy
- **9090**: Prometheus monitoring (optional)

## 🔧 Management Scripts

### build.sh - Build Docker Images

```bash
# Basic build
./build.sh

# Development build
./build.sh --target development

# Build with custom tag and registry
./build.sh --tag v1.0.0 --registry myregistry.com

# Clean build
./build.sh --clean --verbose
```

### run.sh - Manage Services

```bash
# Start services
./run.sh up                    # Foreground
./run.sh up --detach          # Background
./run.sh up --build           # Rebuild first

# Stop services
./run.sh down

# View logs
./run.sh logs --follow

# Check status
./run.sh status

# Run health checks
./run.sh test

# Clean up everything
./run.sh clean
```

### deploy.sh - Production Deployment

```bash
# Local production deployment
./deploy.sh

# Deploy to Docker Hub
./deploy.sh --target docker-hub --version v1.0.0

# Deploy to Kubernetes
./deploy.sh --target kubernetes --ssl

# Deploy to AWS
./deploy.sh --target aws --registry myregistry.com

# Rollback deployment
./deploy.sh --rollback
```

## 🐳 Docker Services

### korean-learning-app

Main Flask application with Korean NLP support:

- **Image**: Based on Python 3.11 with Korean locale
- **Features**: KoNLPy, Korean fonts, mecab
- **Health Check**: `/api/status` endpoint
- **Resources**: 2GB RAM, 2 CPU cores

### database

PostgreSQL with Korean language support:

- **Image**: PostgreSQL 15 Alpine
- **Encoding**: UTF-8 with ko_KR locale
- **Persistence**: Named volume for data
- **Backup**: Automated daily backups

### cache

Redis for session storage and caching:

- **Image**: Redis 7 Alpine
- **Authentication**: Password protected
- **Persistence**: Optional data persistence

### nginx

Reverse proxy with Korean language optimization:

- **Features**: Rate limiting, SSL support, compression
- **Configuration**: Optimized for Korean characters
- **Security**: Security headers, CORS support

## 🌍 Korean Language Support

### Locale Configuration

```dockerfile
ENV LANG=ko_KR.UTF-8
ENV LANGUAGE=ko_KR:ko
ENV LC_ALL=ko_KR.UTF-8
```

### Korean NLP Dependencies

- **KoNLPy**: Korean natural language processing
- **Mecab**: Morphological analyzer
- **Java 11**: Required for KoNLPy
- **Korean Fonts**: Nanum fonts for text rendering

### Text Processing

- **Encoding**: UTF-8 throughout the stack
- **Similarity**: Cosine similarity for Korean text
- **Stopwords**: Korean-specific stopword filtering
- **POS Tagging**: Noun and verb extraction

## 📊 Monitoring and Health Checks

### Health Endpoints

- **Application**: `GET /api/status`
- **Database**: PostgreSQL connection check
- **Cache**: Redis ping check

### Monitoring Stack (Optional)

```bash
# Enable monitoring
./run.sh up monitoring

# Access Prometheus
open http://localhost:9090
```

### Log Management

```bash
# View application logs
./run.sh logs korean-learning-app --follow

# View all logs
./run.sh logs --follow

# Export logs
docker-compose logs > system.log
```

## 🔒 Security Configuration

### Production Security

```bash
# In .env.docker
SECURE_COOKIES=true
HTTPS_ONLY=true
RATE_LIMIT_ENABLED=true
SECRET_KEY=strong-production-key
```

### SSL/TLS Setup

```bash
# Generate self-signed certificates (development)
mkdir -p ssl
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes

# Deploy with SSL
./deploy.sh --ssl
```

### Network Security

- Services communicate via internal Docker network
- Only necessary ports exposed to host
- Rate limiting on API endpoints
- CORS configuration for cross-origin requests

## 📈 Performance Optimization

### Resource Limits

```yaml
# In docker-compose-complete.yml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '2'
    reservations:
      memory: 1G
      cpus: '1'
```

### Caching Strategy

- **Nginx**: Static file caching
- **Redis**: Session and application caching
- **Database**: Connection pooling
- **Application**: Response caching

### Korean Text Processing

- **Mecab**: Fast morphological analysis
- **Vectorization**: Cached similarity calculations
- **Stopwords**: Optimized Korean stopword lists

## 🚀 Deployment Platforms

### Local Development

```bash
# Development mode
./build.sh --target development
./run.sh up --env development
```

### Docker Hub

```bash
# Build and push to Docker Hub
./deploy.sh --target docker-hub --registry your-username
```

### Kubernetes

```bash
# Deploy to Kubernetes cluster
./deploy.sh --target kubernetes --namespace korean-learning
```

### Cloud Platforms

```bash
# AWS ECS deployment
./deploy.sh --target aws --registry your-ecr-registry

# Google Cloud Run (coming soon)
./deploy.sh --target gcp

# Azure Container Instances (coming soon)
./deploy.sh --target azure
```

## 🧪 Testing and Validation

### Automated Tests

```bash
# Run comprehensive tests
./run.sh test

# Health check only
curl http://localhost:8080/api/status
```

### Load Testing

```bash
# Simple load test
for i in {1..100}; do
  curl -s http://localhost:8080/api/status > /dev/null &
done
wait
```

### Korean Text Testing

```bash
# Test Korean text processing
curl -X POST http://localhost:8080/api/similarity \
  -H "Content-Type: application/json" \
  -d '{"text1": "한국어 처리", "text2": "한글 분석"}'
```

## 🔧 Troubleshooting

### Common Issues

1. **Port Conflicts**: Change ports in `.env.docker`
2. **Memory Issues**: Increase Docker memory allocation
3. **Korean Text Issues**: Verify locale and font installation
4. **Database Connection**: Check database service health

### Debug Commands

```bash
# Check service logs
./run.sh logs korean-learning-app

# Inspect container
docker exec -it korean-learning-main bash

# Check Korean locale
docker exec korean-learning-main locale

# Test Korean text processing
docker exec korean-learning-main python -c "import konlpy; print('KoNLPy working')"
```

### Performance Issues

```bash
# Monitor resource usage
docker stats

# Check database performance
./run.sh logs database | grep slow

# Profile application
docker exec korean-learning-main python -m cProfile app/main.py
```

## 📚 Educational Features

### 4-Phase Learning System

1. **Phase 1**: Sentence component identification
2. **Phase 2**: Importance assessment
3. **Phase 3**: Concept generalization
4. **Phase 4**: Topic reconstruction

### Teacher Dashboard

- Real-time student monitoring
- Performance analytics
- Intervention recommendations
- Class management tools

### Legacy Quiz System

- Multiple choice questions
- Free response evaluation
- Korean text similarity scoring
- Backward compatibility

## 📝 Maintenance

### Regular Tasks

```bash
# Update images
./build.sh --clean
./run.sh restart

# Backup database
docker exec korean-learning-db pg_dump -U korean_user korean_learning > backup.sql

# Clean up unused resources
docker system prune -f
```

### Version Updates

```bash
# Tag new version
./build.sh --tag v1.1.0

# Deploy new version
./deploy.sh --version v1.1.0

# Rollback if needed
./deploy.sh --rollback
```

## 🤝 Contributing

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd korean-learning-system

# Setup development environment
cp .env.docker .env
./build.sh --target development
./run.sh up --env development
```

### Testing Changes

```bash
# Run tests
./run.sh test

# Test Korean NLP features
python -m pytest tests/test_korean_nlp.py

# Validate Docker configuration
docker-compose config
```

## 📄 License

This Docker deployment configuration is part of the Korean Learning System project.

## 🆘 Support

For deployment issues:

1. Check logs: `./run.sh logs --follow`
2. Verify configuration: `docker-compose config`
3. Test health endpoints: `./run.sh test`
4. Review Korean language setup in containers

---

**Happy Learning! 🎓 한국어 독해 학습 시스템에 오신 것을 환영합니다!**