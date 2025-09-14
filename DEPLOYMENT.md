# Korean Reading JSON System - Deployment Guide

## Architecture Overview

The system consists of the following services:
- **PostgreSQL**: Primary database for all application data
- **Redis**: Cache and session storage
- **RabbitMQ**: Message queue for background tasks
- **Generator**: Content generation service
- **Grader**: Submission grading service
- **Student API**: FastAPI service for student operations
- **Admin API**: FastAPI service for administrative operations
- **Celery Worker**: Background task processor
- **Celery Beat**: Scheduled task manager
- **Frontend**: React application
- **Nginx**: Reverse proxy and load balancer

## Prerequisites

- Docker Engine 20.10+ 
- Docker Compose 2.0+
- 8GB RAM minimum (16GB recommended for production)
- 20GB free disk space

## Quick Start (Development)

1. Clone the repository and navigate to the project directory
2. Copy the environment file:
   ```bash
   cp .env.example .env
   ```

3. Run the setup command:
   ```bash
   make setup
   ```

This will:
- Build all Docker images
- Start all services
- Initialize the database
- Run migrations

4. Access the services:
   - Frontend: http://localhost:3000
   - Student API: http://localhost:8001/docs
   - Admin API: http://localhost:8002/docs
   - RabbitMQ Management: http://localhost:15672 (rabbit_admin/rabbit_password_123)

## Production Deployment

### 1. Environment Configuration

Edit `.env` file with production values:
```bash
# Change all default passwords
DB_PASSWORD=<strong_password>
REDIS_PASSWORD=<strong_password>
RABBITMQ_PASSWORD=<strong_password>
JWT_SECRET=<generated_secret_key>

# Set production URLs
FRONTEND_API_URL=https://api.yourdomain.com
CORS_ORIGINS=https://yourdomain.com

# Configure email
SMTP_HOST=your-smtp-server.com
SMTP_USER=your-email@domain.com
SMTP_PASSWORD=<email_password>
```

### 2. SSL Configuration

Place SSL certificates in `infrastructure/nginx/ssl/`:
```bash
infrastructure/nginx/ssl/
├── cert.pem
└── key.pem
```

### 3. Deploy to Production

```bash
ENV=production make deploy-prod
```

### 4. Database Backup Strategy

Set up automated backups:
```bash
# Manual backup
make db-backup

# Restore from backup
make db-restore BACKUP=backup_20240101_120000.sql.gz
```

Add to crontab for automated daily backups:
```cron
0 2 * * * cd /path/to/project && make db-backup
```

## Service Management

### Starting and Stopping Services

```bash
# Start all services
make up

# Stop all services
make down

# Restart specific service
docker-compose restart <service-name>

# View logs
make logs
make logs-service SERVICE=student-api
```

### Health Monitoring

```bash
# Check all services health
make check-health

# Monitor services in real-time
make monitor-services
```

### Scaling Services

```bash
# Scale worker instances
docker-compose up -d --scale celery-worker=3

# Scale API instances (update docker-compose.yml for permanent changes)
docker-compose up -d --scale student-api=2
```

## Maintenance Operations

### Database Migrations

```bash
# Apply migrations
make db-migrate

# Rollback last migration
make db-rollback

# Reset database (WARNING: destroys all data)
make db-reset
```

### Maintenance Mode

```bash
# Enable maintenance mode
make maintenance-on

# Disable maintenance mode
make maintenance-off
```

### Updating Services

1. Pull latest code
2. Build new images:
   ```bash
   make build
   ```
3. Apply database migrations:
   ```bash
   make db-migrate
   ```
4. Restart services:
   ```bash
   make restart
   ```

## Troubleshooting

### Common Issues

1. **Port conflicts**
   - Change port mappings in `.env` file
   - Check for conflicting services: `netstat -tulpn | grep <port>`

2. **Database connection errors**
   - Verify PostgreSQL is running: `docker-compose ps postgres`
   - Check credentials in `.env`
   - Ensure database exists: `make shell-db`

3. **Redis connection errors**
   - Check Redis is running: `docker-compose ps redis`
   - Verify password in `.env`
   - Test connection: `make redis-cli`

4. **Frontend not loading**
   - Check nginx logs: `docker-compose logs nginx`
   - Verify API endpoints are accessible
   - Clear browser cache

### Debug Commands

```bash
# Access service shells
make shell-generator
make shell-grader
make shell-student-api
make shell-admin-api

# Database shell
make shell-db

# Redis CLI
make redis-cli

# View detailed logs
docker-compose logs -f --tail=100 <service-name>
```

## Performance Optimization

### Database Optimization

1. Add indexes for frequently queried fields (already included in init.sql)
2. Configure PostgreSQL for your hardware:
   ```yaml
   # In docker-compose.prod.yml
   postgres:
     command: 
       - postgres
       - -c
       - shared_buffers=256MB
       - -c
       - max_connections=200
   ```

### Redis Configuration

Production Redis configuration in docker-compose.prod.yml:
- Uses AOF persistence
- Sets memory limit and eviction policy
- Configures maxmemory-policy for LRU eviction

### Nginx Tuning

Configuration includes:
- Gzip compression
- Static file caching
- Rate limiting
- Connection pooling

## Security Checklist

- [ ] Change all default passwords in `.env`
- [ ] Configure SSL certificates
- [ ] Set up firewall rules
- [ ] Enable database backups
- [ ] Configure log rotation
- [ ] Set up monitoring alerts
- [ ] Review CORS settings
- [ ] Enable rate limiting
- [ ] Configure secure headers
- [ ] Set up fail2ban or similar

## Monitoring and Alerting

### Prometheus Metrics

Services expose metrics on `/metrics` endpoint:
- http://localhost:8001/metrics (Student API)
- http://localhost:8002/metrics (Admin API)

### Health Checks

All services include health check endpoints:
- `/health` - Basic health check
- `/ready` - Readiness check (includes dependencies)

### Log Aggregation

Logs are stored in Docker's json-file driver with rotation:
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## Rollback Procedures

### Application Rollback

1. Stop current deployment:
   ```bash
   ENV=production make down
   ```

2. Checkout previous version:
   ```bash
   git checkout <previous-tag>
   ```

3. Rebuild and deploy:
   ```bash
   ENV=production make deploy-prod
   ```

### Database Rollback

```bash
# Rollback last migration
ENV=production make db-rollback

# Restore from backup
make db-restore BACKUP=<backup-file>
```

## Support and Resources

- Documentation: `/CLAUDE.md`
- API Documentation: Available at `/docs` endpoint for each API
- RabbitMQ Management: http://localhost:15672
- Database Schema: `/infrastructure/postgres/init.sql`

## Contact

For issues or questions, refer to the project documentation or contact the development team.