#!/bin/bash

# Korean Reading Comprehension System - Docker Setup Validation Script

echo "======================================"
echo "Docker Setup Validation"
echo "======================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Validation counters
ERRORS=0
WARNINGS=0

# Function to check if file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $2 exists"
    else
        echo -e "${RED}✗${NC} $2 missing"
        ERRORS=$((ERRORS + 1))
    fi
}

# Function to check if directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $2 directory exists"
    else
        echo -e "${YELLOW}⚠${NC} $2 directory missing (will be created)"
        WARNINGS=$((WARNINGS + 1))
    fi
}

# Function to check Docker daemon
check_docker() {
    if docker info >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Docker daemon is running"
        
        # Check Docker Compose
        if docker compose version >/dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Docker Compose v2 is available"
        else
            echo -e "${RED}✗${NC} Docker Compose v2 not found"
            ERRORS=$((ERRORS + 1))
        fi
    else
        echo -e "${RED}✗${NC} Docker daemon is not running"
        ERRORS=$((ERRORS + 1))
    fi
}

# Function to check environment variables
check_env() {
    if [ -f ".env" ]; then
        echo -e "${GREEN}✓${NC} .env file exists"
        
        # Check for required API keys
        if grep -q "OPENAI_API_KEY=your_openai_api_key_here" .env; then
            echo -e "${YELLOW}⚠${NC} OPENAI_API_KEY not configured"
            WARNINGS=$((WARNINGS + 1))
        fi
        
        if grep -q "ANTHROPIC_API_KEY=your_anthropic_api_key_here" .env; then
            echo -e "${YELLOW}⚠${NC} ANTHROPIC_API_KEY not configured"
            WARNINGS=$((WARNINGS + 1))
        fi
    else
        echo -e "${RED}✗${NC} .env file missing - copy from .env.example"
        ERRORS=$((ERRORS + 1))
    fi
}

echo "1. Checking Docker Installation"
echo "--------------------------------"
check_docker
echo ""

echo "2. Checking Core Files"
echo "----------------------"
check_file "docker-compose.yml" "docker-compose.yml"
check_file "Dockerfile.web" "Web Interface Dockerfile"
check_file "Dockerfile.analytics" "Analytics Dockerfile"
check_file "Dockerfile.study" "Study System Dockerfile"
check_file "web_interface.py" "Web Interface Application"
check_file "analytics.py" "Analytics Application"
check_file "study_system.py" "Study System Application"
check_file "Makefile" "Makefile"
echo ""

echo "3. Checking Directories"
echo "-----------------------"
check_dir "generator" "Generator"
check_dir "generator/out" "Generator output"
check_dir "grader" "Grader"
check_dir "nginx" "Nginx configuration"
check_dir "nginx/conf.d" "Nginx conf.d"
echo ""

echo "4. Checking Environment Configuration"
echo "-------------------------------------"
check_env
echo ""

echo "5. Checking Port Availability"
echo "-----------------------------"
# Check if ports are available
for port in 5000 5432 6379 8001 8002 3000 80; do
    if lsof -i :$port >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠${NC} Port $port is already in use"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${GREEN}✓${NC} Port $port is available"
    fi
done
echo ""

echo "6. Validation Summary"
echo "--------------------"
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! System is ready.${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Configure your API keys in .env file"
    echo "2. Run 'make build' to build containers"
    echo "3. Run 'make up' to start services"
    echo "4. Access web interface at http://localhost:5000"
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Setup complete with $WARNINGS warning(s)${NC}"
    echo ""
    echo "Review warnings above and proceed with:"
    echo "1. Configure your API keys in .env file"
    echo "2. Run 'make build' to build containers"
    echo "3. Run 'make up' to start services"
else
    echo -e "${RED}✗ Setup validation failed with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    echo ""
    echo "Please fix the errors above before proceeding."
    exit 1
fi

echo ""
echo "======================================"
echo "For help, see DOCKER_SETUP.md"
echo "======================================"