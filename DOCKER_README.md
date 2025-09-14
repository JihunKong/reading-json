# 🎓 Korean Reading Comprehension Learning System - Docker Setup

## 📋 Overview

This Docker-based learning system helps students effectively learn factual reading and summarization strategies through interactive Korean reading comprehension tasks. The system randomly loads JSON task files and provides adaptive learning experiences.

## 🏗️ Architecture

The system consists of multiple containerized services working in parallel:

- **Web Learning Interface** - Flask-based web application with real-time features
- **PostgreSQL Database** - Persistent storage for user sessions and progress
- **Redis Cache** - Session management and caching
- **Analytics Service** - Performance tracking and visualization
- **Nginx Reverse Proxy** - Load balancing and security
- **Prometheus & Grafana** - Monitoring and metrics visualization

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- Docker Compose V2
- At least 4GB available RAM
- Port 80, 443, 3000, 5000, 5432, 6379, 9090 available

### 1. Initial Setup

```bash
# Clone and navigate to the project
cd /Users/jihunkong/reading-json

# Copy environment configuration
cp .env.example .env
# Edit .env to add your API keys

# Build all Docker images
docker compose -f docker-compose.learning.yml build
```

### 2. Start Services

```bash
# Start all services
docker compose -f docker-compose.learning.yml up -d

# Or use the Makefile
make -f Makefile.learning up
```

### 3. Access the Application

- 📚 **Learning Interface**: http://localhost:5000
- 📊 **Grafana Dashboard**: http://localhost:3000 (admin/admin)
- 📈 **Prometheus**: http://localhost:9090
- 🌐 **Nginx**: http://localhost

## 📖 Features

### Learning Strategies
The system implements evidence-based learning methodologies:

1. **Micro-Summarization** - Sentence-level summary practice
2. **Macro-Summarization** - Paragraph/article-level summaries
3. **GIST Method** - Core concept extraction
4. **Reciprocal Teaching** - Four-strategy approach (예측, 질문, 명료화, 요약)

### Adaptive Learning
- Dynamic difficulty adjustment based on performance
- Personalized task selection
- Spaced repetition algorithms
- Real-time progress tracking

### Gamification Elements
- Achievement system with badges
- Learning streaks
- Progress visualization
- Peer comparison features

## 🛠️ Usage Commands

### Using Makefile

```bash
# View all available commands
make -f Makefile.learning help

# Common operations
make -f Makefile.learning build    # Build images
make -f Makefile.learning up       # Start services
make -f Makefile.learning down     # Stop services
make -f Makefile.learning logs     # View logs
make -f Makefile.learning health   # Check health
make -f Makefile.learning stats    # View statistics
```

### Using Docker Compose Directly

```bash
# Start services
docker compose -f docker-compose.learning.yml up -d

# View logs
docker compose -f docker-compose.learning.yml logs -f

# Stop services
docker compose -f docker-compose.learning.yml down

# Clean everything
docker compose -f docker-compose.learning.yml down -v
```

### Generate New Tasks

```bash
# Generate tasks using the existing generator
docker compose run --rm generator python mass_generate.py

# Or generate specific number
docker compose run --rm generator python cli.py generate --count 20
```

## 📊 Monitoring & Analytics

### Grafana Dashboards
1. Access http://localhost:3000
2. Login with admin/admin
3. View pre-configured dashboards:
   - User Performance Overview
   - System Metrics
   - Learning Analytics

### Database Access

```bash
# Connect to PostgreSQL
docker compose -f docker-compose.learning.yml exec postgres psql -U postgres reading_db

# View user statistics
SELECT * FROM user_statistics;

# Check daily performance
SELECT * FROM daily_performance WHERE user_id = 'USER_ID';
```

### Redis Cache

```bash
# Connect to Redis
docker compose -f docker-compose.learning.yml exec redis redis-cli

# View all keys
KEYS *

# Get session data
GET session:USER_ID
```

## 🧪 Testing

### Run System Test
```bash
# Run comprehensive test
./test_docker_setup.sh

# Test API endpoints
make -f Makefile.learning test-flow

# Run unit tests
docker compose run --rm web-learning python -m pytest tests/
```

### Health Checks
```bash
# Check all services
make -f Makefile.learning health

# Individual checks
curl http://localhost:5000/health
curl http://localhost/health
```

## 🔧 Configuration

### Environment Variables
Edit `.env` file:
```env
CLAUDE_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key
SECRET_KEY=your_secret_key
FLASK_ENV=production
LOG_LEVEL=INFO
DATABASE_URL=postgresql://postgres:password@postgres:5432/reading_db
REDIS_URL=redis://redis:6379/0
```

### Nginx Configuration
- Rate limiting: 10 req/s (general), 30 req/s (API)
- Caching: Static files cached for 30 days
- Security headers: XSS protection, frame options, etc.

### Database Configuration
- Automatic user level updates
- Achievement tracking
- Session management
- Analytics views

## 📝 Development

### Local Development
```bash
# Run with hot-reload
docker compose -f docker-compose.learning.yml -f docker-compose.override.yml up

# Access container shell
docker compose -f docker-compose.learning.yml exec web-learning /bin/bash

# View real-time logs
docker compose -f docker-compose.learning.yml logs -f web-learning
```

### Adding New Features
1. Edit source files locally
2. Rebuild specific service: `docker compose build web-learning`
3. Restart service: `docker compose restart web-learning`
4. Check logs: `docker compose logs -f web-learning`

## 🐛 Troubleshooting

### Common Issues

**Services not starting**
```bash
# Check port conflicts
lsof -i :5000
lsof -i :5432

# Reset everything
docker compose -f docker-compose.learning.yml down -v
docker system prune -f
```

**Database connection errors**
```bash
# Check database is running
docker compose -f docker-compose.learning.yml exec postgres pg_isready

# Recreate database
docker compose -f docker-compose.learning.yml exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS reading_db; CREATE DATABASE reading_db;"
```

**No task files found**
```bash
# Generate tasks
docker compose run --rm generator python mass_generate.py

# Check files exist
docker compose -f docker-compose.learning.yml exec web-learning ls -la generator/out/
```

## 🔒 Security Notes

- All services run as non-root users
- Secrets managed via environment variables
- Network isolation between services
- Rate limiting on API endpoints
- SSL/TLS ready configuration

## 📚 Learning Flow

1. **Student Registration** - Automatic session creation
2. **Adaptive Task Selection** - Based on current level
3. **Reading Phase** - With highlighting and annotation tools
4. **Question Answering** - Three types of questions per task
5. **Immediate Feedback** - With detailed explanations
6. **Progress Tracking** - Real-time analytics
7. **Achievement Unlocking** - Gamification rewards

## 🤝 Support

For issues or questions:
1. Check logs: `make -f Makefile.learning logs`
2. Run health check: `make -f Makefile.learning health`
3. Review this documentation
4. Check container status: `docker compose ps`

## 📈 Performance Tips

- Allocate at least 4GB RAM to Docker
- Use SSD for better database performance
- Enable Docker BuildKit: `export DOCKER_BUILDKIT=1`
- Regularly clean unused images: `docker system prune`

## 🎯 Next Steps

After successful setup:
1. Generate initial task set (100+ tasks)
2. Configure Grafana dashboards
3. Set up backup automation
4. Configure SSL certificates for production
5. Implement additional learning strategies

---

**Version**: 1.0.0  
**Last Updated**: 2025  
**System Type**: Dockerized Korean Reading Comprehension Learning System