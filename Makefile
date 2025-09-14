.PHONY: help setup build up down restart logs clean test

# Default target
help:
	@echo "Korean Reading Comprehension System - Available Commands"
	@echo "========================================================="
	@echo "Setup & Build:"
	@echo "  make setup          - Initial setup (copy .env, build, init DB)"
	@echo "  make build          - Build all Docker containers"
	@echo "  make rebuild        - Force rebuild all containers"
	@echo ""
	@echo "Container Management:"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make ps             - Show running containers"
	@echo "  make logs           - View all logs"
	@echo "  make logs-f         - Follow logs in real-time"
	@echo ""
	@echo "Content Generation:"
	@echo "  make gen-para       - Generate 5 paragraph tasks"
	@echo "  make gen-art        - Generate 3 article tasks"
	@echo "  make gen-batch      - Generate batch content (10 each)"
	@echo ""
	@echo "Grading & Testing:"
	@echo "  make grade-sample   - Grade sample submissions"
	@echo "  make test-api       - Test API endpoints"
	@echo "  make test-all       - Run all tests"
	@echo ""
	@echo "Database Management:"
	@echo "  make db-shell       - Access PostgreSQL shell"
	@echo "  make db-backup      - Backup database"
	@echo "  make db-restore     - Restore database from backup"
	@echo "  make db-migrate     - Run database migrations"
	@echo ""
	@echo "Service Access:"
	@echo "  make shell-api      - Access Student API shell"
	@echo "  make shell-admin    - Access Admin API shell"
	@echo "  make shell-worker   - Access Worker shell"
	@echo "  make redis-cli      - Access Redis CLI"
	@echo "  make rabbitmq-ui    - Open RabbitMQ Management UI"
	@echo ""
	@echo "Monitoring:"
	@echo "  make health         - Check all services health"
	@echo "  make stats          - Show system statistics"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Remove generated files"
	@echo "  make clean-all      - Remove all data and volumes"
	@echo "  make prune          - Remove unused Docker resources"

# Setup & Build Commands
setup:
	@echo "Setting up Korean Reading Comprehension System..."
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env file"; fi
	@docker compose build
	@docker compose up -d postgres redis rabbitmq
	@echo "Waiting for services to be ready..."
	@sleep 10
	@docker compose up -d
	@echo "Setup complete! Access the application at http://localhost:3000"

build:
	docker compose build

rebuild:
	docker compose build --no-cache

# Container Management
up:
	docker compose up -d
	@echo "Services started. Access points:"
	@echo "  - Student Interface: http://localhost:3000"
	@echo "  - Student API: http://localhost:8001/docs"
	@echo "  - Admin API: http://localhost:8002/docs"
	@echo "  - RabbitMQ Management: http://localhost:15672"

down:
	docker compose down

restart:
	docker compose restart

ps:
	docker compose ps

logs:
	docker compose logs

logs-f:
	docker compose logs -f

# Content Generation
gen-para:
	docker compose run --rm generator python cli.py generate --count 5 --mode paragraph

gen-art:
	docker compose run --rm generator python cli.py generate --count 3 --mode article

gen-batch:
	docker compose run --rm generator python cli.py generate --count 10 --mode paragraph
	docker compose run --rm generator python cli.py generate --count 10 --mode article

gen-custom:
	@read -p "Enter mode (paragraph/article): " mode; \
	read -p "Enter count: " count; \
	read -p "Enter difficulty (easy/medium/hard): " diff; \
	docker compose run --rm generator python cli.py generate --count $$count --mode $$mode --difficulty $$diff

# Grading & Testing
grade-sample:
	docker compose run --rm grader python cli.py grade-sample --input grader/samples/submissions.csv

test-api:
	docker compose exec student-api pytest tests/ -v

test-all:
	docker compose exec student-api pytest tests/ -v
	docker compose exec admin-api pytest tests/ -v
	docker compose exec worker pytest tests/ -v

# Database Management
db-shell:
	docker compose exec postgres psql -U postgres -d reading_db

db-backup:
	@mkdir -p backups
	docker compose exec postgres pg_dump -U postgres reading_db > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Database backed up to backups/"

db-restore:
	@echo "Available backups:"
	@ls -la backups/*.sql 2>/dev/null || echo "No backups found"
	@read -p "Enter backup filename: " file; \
	docker compose exec -T postgres psql -U postgres reading_db < backups/$$file

db-migrate:
	docker compose exec student-api alembic upgrade head
	docker compose exec admin-api alembic upgrade head

db-reset:
	docker compose down -v postgres
	docker compose up -d postgres
	@sleep 5
	@echo "Database reset complete"

# Service Shell Access
shell-api:
	docker compose exec student-api /bin/bash

shell-admin:
	docker compose exec admin-api /bin/bash

shell-worker:
	docker compose exec worker /bin/bash

shell-generator:
	docker compose exec generator /bin/bash

shell-grader:
	docker compose exec grader /bin/bash

shell-web:
	docker compose exec web-interface /bin/bash

shell-analytics:
	docker compose exec analytics /bin/bash

shell-study:
	docker compose exec -it study-cli /bin/bash

# Redis & RabbitMQ Access
redis-cli:
	docker compose exec redis redis-cli -a redis123

rabbitmq-ui:
	@echo "Opening RabbitMQ Management UI..."
	@echo "URL: http://localhost:15672"
	@echo "Username: admin"
	@echo "Password: admin123"
	@open http://localhost:15672 2>/dev/null || xdg-open http://localhost:15672 2>/dev/null || echo "Please open http://localhost:15672 in your browser"

# Web Interface & Analytics Management
web-start:
	docker compose up -d web-interface
	@echo "Web interface started at http://localhost:5000"

web-stop:
	docker compose stop web-interface

web-restart:
	docker compose restart web-interface

analytics-start:
	docker compose up -d analytics
	@echo "Analytics service started"

analytics-stop:
	docker compose stop analytics

study-cli:
	docker compose run --rm -it study-cli

logs-web:
	docker compose logs -f web-interface

logs-analytics:
	docker compose logs -f analytics

# Monitoring
health:
	@echo "Checking service health..."
	@curl -s http://localhost:8001/health | python -m json.tool || echo "Student API: Unhealthy"
	@curl -s http://localhost:8002/health | python -m json.tool || echo "Admin API: Unhealthy"
	@curl -s http://localhost:5000/health | python -m json.tool || echo "Web Interface: Unhealthy"
	@docker compose exec postgres pg_isready -U postgres || echo "PostgreSQL: Unhealthy"
	@docker compose exec redis redis-cli -a redis123 ping || echo "Redis: Unhealthy"

stats:
	@echo "System Statistics:"
	@echo "=================="
	@docker stats --no-stream
	@echo ""
	@echo "Database Stats:"
	@docker compose exec postgres psql -U postgres -d reading_db -c "SELECT 'Users' as table_name, COUNT(*) as count FROM users UNION SELECT 'Content Items', COUNT(*) FROM content_items UNION SELECT 'Submissions', COUNT(*) FROM submissions;"

monitor:
	watch -n 2 "docker compose ps && echo '' && docker stats --no-stream"

# Cleanup
clean:
	rm -rf generator/out/*
	rm -rf grader/reports/*
	@echo "Cleaned generated files"

clean-all:
	docker compose down -v
	rm -rf generator/out/*
	rm -rf grader/reports/*
	rm -rf backups/*
	@echo "Cleaned all data and volumes"

prune:
	docker system prune -f
	docker volume prune -f
	@echo "Pruned unused Docker resources"

# Development Commands
dev-frontend:
	docker compose up frontend

dev-api:
	docker compose up student-api admin-api

dev-worker:
	docker compose up worker

# Production Commands
prod-build:
	BUILD_TARGET=production docker compose -f docker-compose.yml -f docker-compose.prod.yml build

prod-up:
	BUILD_TARGET=production docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-deploy:
	@echo "Deploying to production..."
	$(MAKE) prod-build
	$(MAKE) prod-up
	$(MAKE) db-migrate
	@echo "Production deployment complete"

# Testing specific components
test-generator:
	docker compose run --rm generator python -m pytest tests/ -v

test-grader:
	docker compose run --rm grader python -m pytest tests/ -v

test-integration:
	docker compose run --rm -e INTEGRATION_TEST=true student-api pytest tests/integration/ -v

# Utility commands
version:
	@echo "Korean Reading Comprehension System v1.0.0"
	@docker compose version
	@docker version --format "Docker {{.Server.Version}}"

check-env:
	@if [ ! -f .env ]; then echo "ERROR: .env file not found. Run 'make setup' first."; exit 1; fi
	@echo ".env file exists"
	@grep -E "^[A-Z_]+=" .env | wc -l | xargs echo "Environment variables configured:"

# Performance testing
load-test:
	@echo "Running load test on Student API..."
	docker run --rm --network reading-json_reading-net \
		-v $(PWD)/tests/load:/scripts \
		loadimpact/k6 run /scripts/student-api-load.js

# Backup all data
backup-all:
	@mkdir -p backups/$(shell date +%Y%m%d)
	$(MAKE) db-backup
	tar -czf backups/$(shell date +%Y%m%d)/content.tar.gz generator/out/
	tar -czf backups/$(shell date +%Y%m%d)/reports.tar.gz grader/reports/
	@echo "Full backup completed in backups/$(shell date +%Y%m%d)/"