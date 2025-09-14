# Korean Reading Comprehension System - Production Troubleshooting Guide

## Table of Contents

1. [Quick Diagnostic Commands](#quick-diagnostic-commands)
2. [Container Issues](#container-issues)
3. [Database Problems](#database-problems)
4. [Network and Connectivity](#network-and-connectivity)
5. [Performance Issues](#performance-issues)
6. [Korean Language Specific](#korean-language-specific)
7. [Security and Authentication](#security-and-authentication)
8. [Monitoring and Logging](#monitoring-and-logging)
9. [Emergency Recovery](#emergency-recovery)
10. [Common Error Messages](#common-error-messages)

## Quick Diagnostic Commands

### System Health Overview
```bash
# Overall system status
docker-compose ps
docker stats --no-stream

# Check all health endpoints
curl -s http://localhost/health | jq '.'
curl -s http://localhost:8001/health | jq '.'
curl -s http://localhost:8002/health | jq '.'

# Quick log check for errors
docker-compose logs --tail=50 | grep -i error

# Resource usage summary
df -h
free -h
docker system df
```

### Service-Specific Diagnostics
```bash
# Web application
docker-compose exec web python -c "from config.config import get_config; print(get_config().environment)"

# Database connectivity
docker-compose exec web python -c "
from database.db_manager import get_database_manager
db = get_database_manager()
print('Database connection: OK')
"

# Redis connectivity
docker-compose exec web python -c "
import redis
from config.secrets import get_redis_url
r = redis.from_url(get_redis_url())
print('Redis ping:', r.ping())
"

# Worker status
docker-compose exec worker celery -A tasks inspect active
```

## Container Issues

### Container Won't Start

**Symptoms:**
- Container exits immediately
- "Exited (1)" or "Exited (125)" status
- Container restarts continuously

**Diagnostic Steps:**
```bash
# Check container logs
docker-compose logs service-name

# Check container exit code
docker-compose ps

# Inspect container configuration
docker-compose config

# Check if port is already in use
netstat -tulpn | grep :5000

# Verify environment variables
docker-compose exec service-name env | grep -E "(DB_|REDIS_|SECRET)"
```

**Common Solutions:**
```bash
# Rebuild container with no cache
docker-compose build --no-cache service-name

# Check for missing environment variables
docker-compose exec service-name printenv | sort

# Verify file permissions
docker-compose exec service-name ls -la /app/

# Clean up old containers and networks
docker system prune -f
docker-compose down --remove-orphans
```

### Out of Memory (OOM) Issues

**Symptoms:**
- Container killed unexpectedly
- Error 137 exit code
- Performance degradation

**Diagnostic Steps:**
```bash
# Check memory usage
docker stats --no-stream
free -h
cat /proc/meminfo

# Check container memory limits
docker inspect container-name | grep -i memory

# Check for memory leaks
docker-compose exec web python -c "
import psutil
process = psutil.Process()
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"
```

**Solutions:**
```bash
# Increase memory limits in docker-compose.yml
services:
  web:
    deploy:
      resources:
        limits:
          memory: 2G

# Restart services to clear memory
docker-compose restart

# Enable swap if not available
sudo swapon --show
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Disk Space Issues

**Symptoms:**
- "No space left on device" errors
- Container cannot write files
- Database operations fail

**Diagnostic Steps:**
```bash
# Check disk usage
df -h
docker system df

# Check Docker volumes
docker volume ls
docker volume inspect volume-name

# Large log files
du -sh /var/lib/docker/containers/*/
find /var/log -name "*.log" -size +100M
```

**Solutions:**
```bash
# Clean up Docker resources
docker system prune -f --volumes
docker image prune -a -f

# Rotate log files
docker-compose exec web logrotate /etc/logrotate.conf

# Move large directories to different partition
sudo mv /var/lib/docker /data/docker
sudo ln -s /data/docker /var/lib/docker
```

## Database Problems

### Connection Refused/Timeout

**Symptoms:**
- "connection refused" errors
- "timeout expired" messages
- Unable to connect to PostgreSQL

**Diagnostic Steps:**
```bash
# Check PostgreSQL container status
docker-compose ps postgres

# Test database connectivity
docker-compose exec postgres pg_isready -U postgres

# Check connection parameters
docker-compose exec web python -c "
from config.secrets import get_database_url
print(get_database_url())
"

# Verify network connectivity
docker-compose exec web nc -zv postgres 5432
```

**Solutions:**
```bash
# Restart PostgreSQL container
docker-compose restart postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Verify database credentials
docker-compose exec postgres psql -U postgres -l

# Reset connection pool
docker-compose restart web worker
```

### Database Migration Failures

**Symptoms:**
- "relation does not exist" errors
- Migration scripts fail
- Schema inconsistencies

**Diagnostic Steps:**
```bash
# Check migration status
docker-compose exec web python -c "
from database.db_manager import MigrationManager, get_database_manager
mm = MigrationManager(get_database_manager())
print('Applied migrations:', mm.get_applied_migrations())
print('Pending migrations:', mm.get_pending_migrations())
"

# Check database schema
docker-compose exec postgres psql -U postgres reading_db -c "\dt"

# Verify migration files
ls -la database/migrations/
```

**Solutions:**
```bash
# Run migrations manually
docker-compose exec web python -c "
from database.db_manager import initialize_database
initialize_database()
"

# Reset database (CAUTION: Data loss)
docker-compose down
docker volume rm project_postgres_data
docker-compose up -d postgres
# Wait for PostgreSQL to start
docker-compose exec web python -c "
from database.db_manager import initialize_database
initialize_database()
"

# Restore from backup
docker-compose exec postgres psql -U postgres reading_db < backup.sql
```

### Poor Database Performance

**Symptoms:**
- Slow query responses
- High CPU usage on PostgreSQL
- Connection pool exhausted

**Diagnostic Steps:**
```bash
# Check active connections
docker-compose exec postgres psql -U postgres -c "
SELECT count(*), state FROM pg_stat_activity GROUP BY state;
"

# Find slow queries
docker-compose exec postgres psql -U postgres -c "
SELECT query, mean_time, calls FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;
"

# Check connection pool status
docker-compose exec web python -c "
from database.db_manager import get_database_manager
db = get_database_manager()
if hasattr(db, 'get_pool_status'):
    print(db.get_pool_status())
"
```

**Solutions:**
```bash
# Optimize PostgreSQL configuration
# Add to docker-compose.yml:
postgres:
  command: postgres -c 'max_connections=200' -c 'shared_buffers=256MB'

# Run VACUUM ANALYZE
docker-compose exec postgres psql -U postgres reading_db -c "VACUUM ANALYZE;"

# Increase connection pool size
# Update config/production.env:
DB_POOL_SIZE=30
DB_MAX_OVERFLOW=50
```

## Network and Connectivity

### Service Discovery Issues

**Symptoms:**
- Services cannot reach each other
- "Name resolution failure" errors
- Intermittent connectivity

**Diagnostic Steps:**
```bash
# Check Docker networks
docker network ls
docker network inspect project_reading-net

# Test service-to-service connectivity
docker-compose exec web ping postgres
docker-compose exec web nc -zv redis 6379

# Check DNS resolution
docker-compose exec web nslookup postgres
docker-compose exec web cat /etc/hosts
```

**Solutions:**
```bash
# Recreate networks
docker-compose down
docker network prune -f
docker-compose up -d

# Use explicit service names
# In docker-compose.yml, ensure consistent naming

# Check firewall rules
sudo iptables -L
sudo ufw status
```

### Load Balancer Issues

**Symptoms:**
- 502 Bad Gateway errors
- Uneven load distribution
- Health check failures

**Diagnostic Steps:**
```bash
# Check Nginx status
docker-compose logs nginx

# Test upstream connectivity
docker-compose exec nginx nc -zv web 5000

# Check Nginx configuration
docker-compose exec nginx nginx -t

# Monitor upstream health
curl -I http://localhost/health
```

**Solutions:**
```bash
# Reload Nginx configuration
docker-compose exec nginx nginx -s reload

# Update upstream configuration
# Edit nginx/conf.d/default.conf

# Add health checks to upstream
upstream backend {
    server web1:5000 max_fails=3 fail_timeout=30s;
    server web2:5000 max_fails=3 fail_timeout=30s;
}
```

## Performance Issues

### High Memory Usage

**Symptoms:**
- System becomes unresponsive
- OOM killer activates
- Swap usage increases

**Diagnostic Steps:**
```bash
# Memory breakdown by service
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Check for memory leaks
docker-compose exec web python -c "
import gc, psutil
print('Objects in memory:', len(gc.get_objects()))
print('Memory usage:', psutil.Process().memory_info().rss / 1024 / 1024, 'MB')
"

# Profile memory usage
docker-compose exec web python -c "
import tracemalloc
tracemalloc.start()
# Run your application code
current, peak = tracemalloc.get_traced_memory()
print(f'Current memory usage: {current / 1024 / 1024:.2f} MB')
print(f'Peak memory usage: {peak / 1024 / 1024:.2f} MB')
"
```

**Solutions:**
```bash
# Implement memory limits
services:
  web:
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

# Enable garbage collection
docker-compose exec web python -c "
import gc
gc.set_threshold(700, 10, 10)
gc.collect()
print('Garbage collection completed')
"

# Restart services periodically
# Add to crontab:
0 2 * * * docker-compose restart web
```

### High CPU Usage

**Symptoms:**
- CPU constantly at 100%
- Slow response times
- System becomes sluggish

**Diagnostic Steps:**
```bash
# CPU usage by container
docker stats --no-stream

# Process monitoring inside container
docker-compose exec web top
docker-compose exec web ps aux

# Python profiling
docker-compose exec web python -c "
import cProfile
import pstats
# Profile your application
"
```

**Solutions:**
```bash
# Scale horizontally
docker-compose up -d --scale web=3 --scale worker=5

# Optimize code paths
# Review database queries
# Implement caching
# Use async operations

# Add CPU limits
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '0.5'
```

### Slow Response Times

**Symptoms:**
- Page load times > 5 seconds
- API timeouts
- Poor user experience

**Diagnostic Steps:**
```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost/health

# Database query performance
docker-compose exec postgres psql -U postgres -c "
SELECT query, mean_time, calls, total_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;
"

# Cache hit rates
docker-compose exec redis redis-cli info stats | grep hit
```

**Solutions:**
```bash
# Enable caching
ENABLE_CACHING=true
CACHE_TTL_SECONDS=3600

# Optimize database queries
# Add appropriate indexes
# Use query optimization

# Enable compression
ENABLE_COMPRESSION=true

# Use CDN for static files
ENABLE_CDN=true
```

## Korean Language Specific

### Font Loading Issues

**Symptoms:**
- Korean text appears as boxes
- Font rendering is poor
- Slow font loading

**Diagnostic Steps:**
```bash
# Check font files
ls -la static/fonts/
curl -I http://localhost/static/fonts/noto_sans_kr-400.woff2

# Test font loading
curl -s http://localhost/static/css/korean-fonts.css

# Check font optimization
docker-compose exec web python -c "
from utils.static_manager import get_static_manager
manager = get_static_manager()
print(manager.font_manager.korean_fonts)
"
```

**Solutions:**
```bash
# Regenerate font CSS
docker-compose exec web python -c "
from utils.static_manager import get_static_manager
manager = get_static_manager()
manager.setup_korean_fonts()
print('Korean fonts setup completed')
"

# Preload critical fonts
# Add to HTML head:
<link rel="preload" href="/static/fonts/noto_sans_kr-400.woff2" as="font" type="font/woff2" crossorigin>

# Check font MIME types
# In nginx configuration:
location ~* \.(woff|woff2|ttf|eot)$ {
    add_header Access-Control-Allow-Origin *;
    expires 1y;
}
```

### Korean Text Processing Errors

**Symptoms:**
- Incorrect text analysis
- Segmentation errors
- NLP processing failures

**Diagnostic Steps:**
```bash
# Test Korean NLP
docker-compose exec web python -c "
from core.nlp.korean_analyzer import KoreanAnalyzer
analyzer = KoreanAnalyzer()
result = analyzer.analyze('안녕하세요 테스트입니다')
print('Analysis result:', result)
"

# Check KoNLPy backend
docker-compose exec web python -c "
import konlpy
from konlpy.tag import Mecab
try:
    mecab = Mecab()
    print('Mecab initialized successfully')
except Exception as e:
    print('Mecab error:', e)
"
```

**Solutions:**
```bash
# Install Korean language support
docker-compose exec web apt-get update
docker-compose exec web apt-get install -y language-pack-ko

# Rebuild with Korean support
# Add to Dockerfile:
RUN apt-get update && apt-get install -y \
    language-pack-ko \
    fonts-noto-cjk \
    mecab \
    mecab-ko \
    mecab-ko-dic

# Set Korean locale
ENV LANG=ko_KR.UTF-8
ENV LC_ALL=ko_KR.UTF-8
```

## Security and Authentication

### JWT Token Issues

**Symptoms:**
- Authentication failures
- "Invalid token" errors
- Session timeouts

**Diagnostic Steps:**
```bash
# Verify JWT secret
docker-compose exec web python -c "
from config.secrets import get_secret
print('JWT secret configured:', bool(get_secret('JWT_SECRET_KEY')))
"

# Test token generation
docker-compose exec web python -c "
import jwt
from config.secrets import get_secret
secret = get_secret('JWT_SECRET_KEY')
token = jwt.encode({'user_id': 1}, secret, algorithm='HS256')
decoded = jwt.decode(token, secret, algorithms=['HS256'])
print('Token test successful:', decoded)
"
```

**Solutions:**
```bash
# Regenerate JWT secret
docker-compose exec web python -c "
import secrets
new_secret = secrets.token_urlsafe(32)
print('New JWT secret:', new_secret)
"

# Clear user sessions
docker-compose exec redis redis-cli FLUSHDB

# Update token expiration
JWT_EXPIRATION_MINUTES=1440  # 24 hours
```

### Permission Denied Errors

**Symptoms:**
- File access denied
- Database permission errors
- Container startup failures

**Diagnostic Steps:**
```bash
# Check file permissions
docker-compose exec web ls -la /app/
docker-compose exec web whoami

# Check database permissions
docker-compose exec postgres psql -U postgres -c "\du"

# Verify volume permissions
sudo ls -la /var/lib/docker/volumes/
```

**Solutions:**
```bash
# Fix file permissions
docker-compose exec web chown -R app:app /app/
docker-compose exec web chmod -R 755 /app/

# Create non-root user in Dockerfile
RUN useradd -r -u 1001 -g root app
USER app

# Fix volume permissions
sudo chown -R 1001:root /var/lib/docker/volumes/project_name/
```

## Monitoring and Logging

### Log Collection Issues

**Symptoms:**
- Missing log entries
- Log rotation failures
- Excessive log size

**Diagnostic Steps:**
```bash
# Check log configuration
docker-compose exec web python -c "
from utils.logging_config import get_logger_manager
manager = get_logger_manager()
print('Logging configuration loaded')
"

# Verify log files
docker-compose exec web ls -la /app/logs/
docker-compose exec web tail -n 20 /app/logs/app.log

# Check disk usage by logs
du -sh /var/lib/docker/containers/*/
```

**Solutions:**
```bash
# Configure log rotation
# Add to docker-compose.yml:
services:
  web:
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"

# Enable structured logging
LOG_FORMAT=json
LOG_LEVEL=INFO

# Clean old logs
find /var/lib/docker/containers/ -name "*.log" -mtime +7 -delete
```

### Metrics Collection Problems

**Symptoms:**
- Prometheus scraping failures
- Missing metrics data
- Grafana connection issues

**Diagnostic Steps:**
```bash
# Test metrics endpoint
curl http://localhost/metrics
curl http://localhost:9090/metrics

# Check Prometheus configuration
docker-compose exec prometheus cat /etc/prometheus/prometheus.yml

# Verify target health
curl http://localhost:9090/api/v1/targets
```

**Solutions:**
```bash
# Restart metrics collection
docker-compose restart prometheus grafana

# Update scrape configuration
# Edit prometheus.yml and reload

# Check network connectivity
docker-compose exec prometheus nc -zv web 5000
```

## Emergency Recovery

### Complete System Failure

**Immediate Actions:**
```bash
# Stop all services
docker-compose down

# Check system resources
df -h && free -h && top

# Restart with minimal services
docker-compose up -d postgres redis
sleep 30
docker-compose up -d web

# Verify core functionality
curl http://localhost/health
```

### Database Corruption

**Recovery Steps:**
```bash
# Stop all services accessing database
docker-compose stop web worker admin-api student-api

# Check database integrity
docker-compose exec postgres pg_dump -U postgres reading_db > emergency_backup.sql

# Restore from latest backup
docker-compose exec postgres psql -U postgres -c "DROP DATABASE reading_db;"
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE reading_db;"
docker-compose exec postgres psql -U postgres reading_db < latest_backup.sql

# Restart services
docker-compose up -d
```

### Data Loss Prevention

**Continuous Backup Strategy:**
```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Database backup
docker-compose exec postgres pg_dump -U postgres reading_db > $BACKUP_DIR/database.sql

# File system backup
docker-compose exec web tar czf $BACKUP_DIR/app_data.tar.gz /app/data/

# Keep only last 7 days
find /backups/ -mtime +7 -type d -exec rm -rf {} \;
```

## Common Error Messages

### "Connection refused"
**Cause:** Service not running or network issue
**Solution:** Check service status and restart if needed

### "No such file or directory"
**Cause:** Missing configuration file or volume mount
**Solution:** Verify file paths and volume mounts

### "Permission denied"
**Cause:** Incorrect file permissions or user context
**Solution:** Fix file ownership and permissions

### "Port already in use"
**Cause:** Another service using the same port
**Solution:** Change port or stop conflicting service

### "Out of memory"
**Cause:** Insufficient RAM or memory leak
**Solution:** Increase memory limits or fix memory leaks

### "Database connection timeout"
**Cause:** Database overloaded or network issue
**Solution:** Check database health and connection pool

### "Invalid JWT token"
**Cause:** Token expired or incorrect secret
**Solution:** Regenerate tokens or fix JWT configuration

### "Korean text not displaying"
**Cause:** Missing Korean fonts or encoding issue
**Solution:** Install Korean fonts and set UTF-8 encoding

---

For additional support, check the logs first, then review the monitoring dashboards before escalating issues.