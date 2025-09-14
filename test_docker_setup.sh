#!/bin/bash

# Test script for Korean Reading Comprehension Docker Setup
# This script verifies that all components are working correctly

set -e

echo "================================================"
echo "Korean Reading Comprehension System Docker Test"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check service
check_service() {
    local service_name=$1
    local check_command=$2
    
    echo -n "Checking $service_name... "
    
    if eval $check_command > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

# Function to test API endpoint
test_api() {
    local endpoint=$1
    local method=$2
    local data=$3
    local expected=$4
    
    echo -n "Testing $endpoint... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000$endpoint)
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" -X $method \
            -H "Content-Type: application/json" \
            -d "$data" \
            http://localhost:5000$endpoint)
    fi
    
    if [ "$response" = "$expected" ]; then
        echo -e "${GREEN}✓${NC} ($response)"
        return 0
    else
        echo -e "${RED}✗${NC} (Expected: $expected, Got: $response)"
        return 1
    fi
}

# Check if Docker is running
echo "1. Checking Docker environment"
echo "-------------------------------"
check_service "Docker" "docker info"
check_service "Docker Compose" "docker compose version"
echo ""

# Build and start services
echo "2. Building Docker images"
echo "-------------------------"
echo "This may take a few minutes on first run..."
docker compose -f docker-compose.learning.yml build
echo -e "${GREEN}Images built successfully${NC}"
echo ""

echo "3. Starting services"
echo "-------------------"
docker compose -f docker-compose.learning.yml up -d
echo "Waiting for services to initialize (15 seconds)..."
sleep 15
echo ""

# Check service health
echo "4. Checking service health"
echo "--------------------------"
check_service "Web Application" "curl -f http://localhost:5000/health"
check_service "PostgreSQL Database" "docker compose -f docker-compose.learning.yml exec -T postgres pg_isready -U postgres"
check_service "Redis Cache" "docker compose -f docker-compose.learning.yml exec -T redis redis-cli ping"
check_service "Nginx Proxy" "curl -f http://localhost/health"
echo ""

# Test API endpoints
echo "5. Testing API endpoints"
echo "------------------------"
test_api "/health" "GET" "" "200"
test_api "/api/get_progress" "GET" "" "200"
test_api "/api/get_task" "POST" '{"strategy":"adaptive"}' "200"
echo ""

# Check database initialization
echo "6. Checking database setup"
echo "--------------------------"
echo -n "Checking tables... "
table_count=$(docker compose -f docker-compose.learning.yml exec -T postgres \
    psql -U postgres -d reading_db -t -c \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")

if [ "$table_count" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} ($table_count tables created)"
else
    echo -e "${RED}✗${NC} (No tables found)"
fi
echo ""

# Check JSON files
echo "7. Checking JSON task files"
echo "---------------------------"
echo -n "Checking task files... "
if docker compose -f docker-compose.learning.yml exec -T web-learning ls generator/out/*.json > /dev/null 2>&1; then
    file_count=$(docker compose -f docker-compose.learning.yml exec -T web-learning ls generator/out/*.json | wc -l)
    echo -e "${GREEN}✓${NC} ($file_count task files found)"
else
    echo -e "${YELLOW}⚠${NC} (No task files found - run 'make generate' to create tasks)"
fi
echo ""

# Check logs for errors
echo "8. Checking logs for errors"
echo "---------------------------"
echo -n "Checking web logs... "
error_count=$(docker compose -f docker-compose.learning.yml logs web-learning 2>&1 | grep -i error | wc -l)
if [ "$error_count" -eq 0 ]; then
    echo -e "${GREEN}✓${NC} (No errors)"
else
    echo -e "${YELLOW}⚠${NC} ($error_count error messages found)"
fi
echo ""

# Display access information
echo "================================================"
echo "System Status Summary"
echo "================================================"
echo ""
echo "Services Running:"
docker compose -f docker-compose.learning.yml ps --format "table {{.Name}}\t{{.Status}}"
echo ""

echo "Access URLs:"
echo "-----------"
echo "📚 Learning Application: http://localhost:5000"
echo "📊 Grafana Dashboard: http://localhost:3000 (admin/admin)"
echo "📈 Prometheus Metrics: http://localhost:9090"
echo "🗄️ PostgreSQL: localhost:5432 (postgres/password)"
echo "💾 Redis: localhost:6379"
echo ""

echo "Next Steps:"
echo "----------"
echo "1. Generate tasks: docker compose -f docker-compose.learning.yml run --rm generator python mass_generate.py"
echo "2. Access the web interface: http://localhost:5000"
echo "3. Monitor with Grafana: http://localhost:3000"
echo "4. View logs: docker compose -f docker-compose.learning.yml logs -f"
echo ""

echo -e "${GREEN}✅ Docker setup test completed successfully!${NC}"
echo ""
echo "To stop all services, run:"
echo "  docker compose -f docker-compose.learning.yml down"
echo ""
echo "To remove all data and start fresh:"
echo "  docker compose -f docker-compose.learning.yml down -v"