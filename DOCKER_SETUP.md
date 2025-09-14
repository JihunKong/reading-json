# Docker Setup Guide - Korean Reading Comprehension System

## Overview

This comprehensive Docker setup provides a production-ready environment for the Korean Reading Comprehension Learning System with the following components:

- **Web Interface**: Flask-based web application for serving learning content
- **Analytics System**: Real-time performance tracking and reporting
- **Study CLI**: Terminal-based interactive learning system
- **Generator**: Content creation service for paragraph and article tasks
- **Grader**: Automated evaluation system for student responses
- **Supporting Services**: PostgreSQL, Redis, RabbitMQ, Nginx

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Nginx (Port 80/443)                  │
├──────────┬────────────┬────────────┬────────────┬──────────┤
│   Web    │   Student  │   Admin    │  Frontend  │ Analytics│
│Interface │    API     │    API     │   (React)  │  Service │
│  :5000   │   :8001    │   :8002    │   :3000    │  (async) │
├──────────┴────────────┴────────────┴────────────┴──────────┤
│                    Shared Infrastructure                     │
├──────────┬────────────┬────────────┬───────────────────────┤
│PostgreSQL│   Redis    │  RabbitMQ  │    File System        │
│  :5432   │   :6379    │   :5672    │  (JSON Task Files)    │
└──────────┴────────────┴────────────┴───────────────────────┘
```

## Quick Start

### 1. Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB+ available RAM
- 10GB+ available disk space

### 2. Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd reading-json

# Copy environment configuration
cp .env.example .env

# Edit .env with your API keys and configuration
nano .env

# Build all containers
make build

# Start all services
make up
```

### 3. Verify Installation

```bash
# Check service health
make health

# View running containers
docker compose ps

# Check logs
make logs
```

## Service URLs

- **Web Interface**: http://localhost:5000
- **Student API**: http://localhost:8001
- **Admin API**: http://localhost:8002
- **Frontend**: http://localhost:3000
- **RabbitMQ Management**: http://localhost:15672 (admin/admin123)
- **Nginx**: http://localhost:80

## Core Services

### Web Interface Service

The Flask web application provides:
- Interactive learning interface
- Real-time content delivery
- Progress tracking
- WebSocket support for live updates

**Configuration**:
```yaml
WEB_INTERFACE_PORT: 5000
FLASK_ENV: production
```

**Access**: http://localhost:5000/study/

### Analytics Service

Continuous analytics processing:
- Performance metrics collection
- Learning pattern analysis
- Report generation
- Prometheus metrics export

**Features**:
- Real-time data processing
- Batch report generation
- Export to multiple formats
- Dashboard integration

### Study CLI System

Interactive terminal-based learning:
```bash
# Launch interactive study session
make study-cli

# Or directly with docker compose
docker compose run --rm -it study-cli
```

## Content Management

### Generate Content

```bash
# Generate 5 paragraph tasks
make gen-para

# Generate 3 article tasks
make gen-art

# Custom generation
docker compose run --rm generator python cli.py generate \
  --count 10 \
  --mode paragraph \
  --difficulty medium \
  --tags "사실적읽기,요약"
```

### Grade Submissions

```bash
# Grade sample submissions
make grade-sample

# Grade custom file
docker compose run --rm grader python cli.py grade \
  --submissions /path/to/submissions.csv
```

## Database Management

### Backup & Restore

```bash
# Create backup
make db-backup

# List backups
ls -la backups/

# Restore from backup
make db-restore
# Then enter the backup filename when prompted
```

### Migrations

```bash
# Run migrations
make db-migrate

# Access database shell
make db-shell
```

## Monitoring & Logging

### View Logs

```bash
# All services
make logs

# Specific service
make logs-web
make logs-analytics
make logs-gen

# Follow logs in real-time
docker compose logs -f web-interface
```

### Health Checks

All services include health checks:
```bash
# Check all services
make health

# Individual health endpoints
curl http://localhost:5000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
```

### Metrics

Prometheus metrics available at:
- Web Interface: http://localhost:5000/metrics
- Analytics: http://localhost:8090/metrics

## Development

### Development Mode

The `docker-compose.override.yml` file automatically enables:
- Hot reload for Python files
- Debug logging
- Source code mounting
- Development tools

### Shell Access

```bash
# Access service shells
make shell-web
make shell-analytics
make shell-study
make shell-generator
make shell-grader
```

### Testing

```bash
# Run all tests
make test

# Test with coverage
make test-coverage

# Test specific service
docker compose exec web-interface pytest tests/
```

## Production Deployment

### 1. Production Configuration

```bash
# Use production compose file
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Or with make
make up-prod
```

### 2. SSL/TLS Setup

Edit `nginx/conf.d/app.conf` to enable SSL:
1. Uncomment the SSL server block
2. Add your certificates to `nginx/ssl/`
3. Restart nginx: `docker compose restart nginx`

### 3. Environment Variables

Critical production settings:
```bash
# Security
SECRET_KEY=<strong-random-key>
JWT_SECRET_KEY=<another-strong-key>
SESSION_COOKIE_SECURE=true

# Database
DB_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>

# API Keys
OPENAI_API_KEY=<your-key>
ANTHROPIC_API_KEY=<your-key>

# Environment
FLASK_ENV=production
APP_ENV=production
DEBUG=false
```

### 4. Resource Limits

Add resource limits in production:
```yaml
services:
  web-interface:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## Troubleshooting

### Common Issues

1. **Port conflicts**
   ```bash
   # Check for port usage
   lsof -i :5000
   lsof -i :5432
   
   # Change ports in .env
   WEB_INTERFACE_PORT=5001
   ```

2. **Memory issues**
   ```bash
   # Increase Docker memory allocation
   # Docker Desktop > Preferences > Resources
   # Set Memory to 4GB minimum
   ```

3. **Permission errors**
   ```bash
   # Fix file permissions
   chmod -R 755 generator/out
   chmod -R 755 grader/reports
   ```

4. **Database connection issues**
   ```bash
   # Reset database
   make db-reset
   
   # Check PostgreSQL logs
   docker compose logs postgres
   ```

### Debug Mode

Enable debug mode for detailed logging:
```bash
# Set in .env
LOG_LEVEL=DEBUG
FLASK_DEBUG=true

# Restart services
make restart
```

## Backup Strategy

### Automated Backups

Create a cron job for regular backups:
```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /path/to/project && make db-backup
```

### Backup Volumes

```bash
# Backup all Docker volumes
docker run --rm \
  -v reading-json_postgres_data:/data/postgres \
  -v reading-json_redis_data:/data/redis \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/volumes_$(date +%Y%m%d).tar.gz /data
```

## Performance Optimization

### 1. Enable Caching

```bash
# In .env
ENABLE_CACHING=true
CACHE_TTL_SECONDS=3600
```

### 2. Configure Workers

```bash
# Adjust based on CPU cores
MAX_WORKERS=4
CONNECTION_POOL_SIZE=20
```

### 3. Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_tasks_type ON tasks(task_type);
CREATE INDEX idx_submissions_user ON submissions(user_id);
```

## Security Best Practices

1. **Change default passwords** in production
2. **Enable firewall** rules for exposed ports
3. **Use SSL/TLS** for all external communications
4. **Implement rate limiting** via Nginx
5. **Regular security updates**: `docker compose pull`
6. **Audit logs** regularly
7. **Use secrets management** for sensitive data

## Maintenance

### Regular Tasks

- **Daily**: Check logs for errors
- **Weekly**: Review analytics reports
- **Monthly**: Update dependencies
- **Quarterly**: Performance review and optimization

### Cleanup

```bash
# Remove unused containers and images
make prune

# Clean generated files
make clean

# Full cleanup (including volumes)
make clean-all
```

## Support

For issues or questions:
1. Check logs: `make logs`
2. Review health status: `make health`
3. Consult this documentation
4. Submit issues to the repository

## License

[Your License Here]