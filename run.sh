#!/bin/bash

# Korean Learning System - Docker Run Script
# This script manages the running of the Korean Learning System Docker containers

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default values
ACTION="up"
ENVIRONMENT="development"
DETACHED=false
BUILD=false
CLEAN=false
TEST=false
FOLLOW_LOGS=false
SERVICES=""
ENV_FILE=".env.docker"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
Korean Learning System - Docker Run Script

Usage: $0 [ACTION] [OPTIONS]

Actions:
    up          Start the services (default)
    down        Stop and remove containers
    restart     Restart the services
    logs        Show service logs
    status      Show service status
    clean       Clean up containers, networks, and volumes
    test        Run health checks and basic tests

Options:
    -e, --env ENV          Environment (development|production) [default: development]
    -d, --detach           Run in detached mode (background)
    -b, --build            Force rebuild images before starting
    -c, --clean            Clean up before starting
    -f, --follow           Follow logs output (for logs action)
    -s, --services LIST    Comma-separated list of services to operate on
    -E, --env-file FILE    Environment file to use [default: .env.docker]
    -t, --test             Run tests after starting services
    -v, --verbose          Enable verbose output
    -h, --help             Show this help message

Examples:
    $0                                    # Start in development mode
    $0 up --env production --detach       # Start in production mode, background
    $0 down                              # Stop all services
    $0 logs --follow                     # Follow logs
    $0 restart --services korean-learning-app,database
    $0 clean                             # Clean up everything
    $0 test                              # Run health checks

Services:
    korean-learning-app   Main Flask application
    database             PostgreSQL database
    cache                Redis cache
    nginx                Reverse proxy
    generator            Content generator (optional)
    monitoring           Prometheus monitoring (optional)

EOF
}

# Parse command line arguments
POSITIONAL_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        up|down|restart|logs|status|clean|test)
            ACTION="$1"
            shift
            ;;
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -d|--detach)
            DETACHED=true
            shift
            ;;
        -b|--build)
            BUILD=true
            shift
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -f|--follow)
            FOLLOW_LOGS=true
            shift
            ;;
        -s|--services)
            SERVICES="$2"
            shift 2
            ;;
        -E|--env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        -t|--test)
            TEST=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            set -x
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        -*|--*)
            print_error "Unknown option $1"
            show_usage
            exit 1
            ;;
        *)
            POSITIONAL_ARGS+=("$1")
            shift
            ;;
    esac
done

# Set positional arguments back
set -- "${POSITIONAL_ARGS[@]}"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|production)$ ]]; then
    print_error "Invalid environment: $ENVIRONMENT (must be 'development' or 'production')"
    exit 1
fi

# Check if Docker and Docker Compose are available
if ! command -v docker >/dev/null 2>&1; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v docker-compose >/dev/null 2>&1 && ! docker compose version >/dev/null 2>&1; then
    print_error "Docker Compose is not available"
    exit 1
fi

# Use docker compose or docker-compose based on availability
if docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Check if environment file exists
if [[ ! -f "$ENV_FILE" ]]; then
    print_warning "Environment file not found: $ENV_FILE"
    if [[ -f ".env.example" ]]; then
        print_status "Copying .env.example to $ENV_FILE"
        cp .env.example "$ENV_FILE"
    else
        print_error "No environment file available. Please create $ENV_FILE"
        exit 1
    fi
fi

# Set compose file and project name
COMPOSE_FILE="docker-compose-complete.yml"
PROJECT_NAME="korean-learning"

# Base docker-compose command
COMPOSE_CMD="$DOCKER_COMPOSE -f $COMPOSE_FILE --env-file $ENV_FILE -p $PROJECT_NAME"

# Add services filter if specified
if [[ -n "$SERVICES" ]]; then
    SERVICES_ARRAY=(${SERVICES//,/ })
else
    SERVICES_ARRAY=()
fi

# Function to check service health
check_service_health() {
    local service=$1
    local max_attempts=30
    local attempt=1
    
    print_status "Checking health of $service..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if $COMPOSE_CMD ps -q "$service" >/dev/null 2>&1; then
            local health_status=$($COMPOSE_CMD ps --format json "$service" 2>/dev/null | jq -r '.[0].Health // "healthy"' 2>/dev/null || echo "unknown")
            
            case "$health_status" in
                "healthy"|"unknown")
                    print_success "$service is healthy"
                    return 0
                    ;;
                "unhealthy")
                    print_error "$service is unhealthy"
                    return 1
                    ;;
                "starting")
                    print_status "$service is starting... (attempt $attempt/$max_attempts)"
                    ;;
                *)
                    print_status "$service status: $health_status (attempt $attempt/$max_attempts)"
                    ;;
            esac
        else
            print_status "$service is not running (attempt $attempt/$max_attempts)"
        fi
        
        sleep 5
        ((attempt++))
    done
    
    print_error "$service failed health check after $max_attempts attempts"
    return 1
}

# Function to run tests
run_tests() {
    print_status "Running Korean Learning System tests..."
    
    # Wait for services to be ready
    sleep 10
    
    # Test main application endpoint
    local app_url="http://localhost:8080"
    if command -v curl >/dev/null 2>&1; then
        if curl -f "$app_url/api/status" >/dev/null 2>&1; then
            print_success "Main application is responding"
        else
            print_error "Main application is not responding at $app_url"
            return 1
        fi
        
        # Test specific endpoints
        local endpoints=(
            "/api/status"
            "/"
        )
        
        for endpoint in "${endpoints[@]}"; do
            if curl -f "$app_url$endpoint" >/dev/null 2>&1; then
                print_success "Endpoint $endpoint is working"
            else
                print_warning "Endpoint $endpoint is not responding"
            fi
        done
    else
        print_warning "curl not available, skipping HTTP tests"
    fi
    
    # Check database connectivity
    if $COMPOSE_CMD exec -T database psql -U korean_user -d korean_learning -c "SELECT 1;" >/dev/null 2>&1; then
        print_success "Database connectivity test passed"
    else
        print_warning "Database connectivity test failed"
    fi
    
    print_success "Tests completed"
}

# Main action handling
case "$ACTION" in
    "up")
        print_status "Starting Korean Learning System ($ENVIRONMENT mode)..."
        
        if [[ "$CLEAN" == "true" ]]; then
            print_status "Cleaning up first..."
            $COMPOSE_CMD down -v --remove-orphans
        fi
        
        # Build if requested
        if [[ "$BUILD" == "true" ]]; then
            print_status "Building images..."
            $COMPOSE_CMD build
        fi
        
        # Start services
        UP_ARGS=""
        if [[ "$DETACHED" == "true" ]]; then
            UP_ARGS="$UP_ARGS -d"
        fi
        
        if [[ "${#SERVICES_ARRAY[@]}" -gt 0 ]]; then
            $COMPOSE_CMD up $UP_ARGS "${SERVICES_ARRAY[@]}"
        else
            $COMPOSE_CMD up $UP_ARGS
        fi
        
        if [[ "$DETACHED" == "true" ]]; then
            print_success "Services started in background"
            
            # Show status
            sleep 5
            $COMPOSE_CMD ps
            
            print_status "To view logs: $0 logs --follow"
            print_status "To stop: $0 down"
        fi
        
        if [[ "$TEST" == "true" ]]; then
            run_tests
        fi
        ;;
        
    "down")
        print_status "Stopping Korean Learning System..."
        
        if [[ "${#SERVICES_ARRAY[@]}" -gt 0 ]]; then
            $COMPOSE_CMD stop "${SERVICES_ARRAY[@]}"
            $COMPOSE_CMD rm -f "${SERVICES_ARRAY[@]}"
        else
            $COMPOSE_CMD down
        fi
        
        print_success "Services stopped"
        ;;
        
    "restart")
        print_status "Restarting Korean Learning System..."
        
        if [[ "${#SERVICES_ARRAY[@]}" -gt 0 ]]; then
            $COMPOSE_CMD restart "${SERVICES_ARRAY[@]}"
        else
            $COMPOSE_CMD restart
        fi
        
        print_success "Services restarted"
        ;;
        
    "logs")
        LOGS_ARGS=""
        if [[ "$FOLLOW_LOGS" == "true" ]]; then
            LOGS_ARGS="$LOGS_ARGS -f"
        fi
        
        if [[ "${#SERVICES_ARRAY[@]}" -gt 0 ]]; then
            $COMPOSE_CMD logs $LOGS_ARGS "${SERVICES_ARRAY[@]}"
        else
            $COMPOSE_CMD logs $LOGS_ARGS
        fi
        ;;
        
    "status")
        print_status "Korean Learning System Status:"
        $COMPOSE_CMD ps
        
        # Check individual service health
        main_services=("korean-learning-app" "database" "cache")
        for service in "${main_services[@]}"; do
            if $COMPOSE_CMD ps -q "$service" >/dev/null 2>&1; then
                check_service_health "$service" || true
            else
                print_warning "$service is not running"
            fi
        done
        ;;
        
    "clean")
        print_warning "This will remove all containers, networks, and volumes!"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Cleaning up Korean Learning System..."
            
            $COMPOSE_CMD down -v --remove-orphans
            
            # Remove unused networks
            docker network prune -f
            
            # Remove unused volumes
            docker volume prune -f
            
            print_success "Cleanup completed"
        else
            print_status "Cleanup cancelled"
        fi
        ;;
        
    "test")
        print_status "Running Korean Learning System health checks..."
        
        # Check if services are running
        if ! $COMPOSE_CMD ps korean-learning-app | grep -q "Up"; then
            print_error "Korean Learning System is not running. Start it first with: $0 up -d"
            exit 1
        fi
        
        run_tests
        ;;
        
    *)
        print_error "Unknown action: $ACTION"
        show_usage
        exit 1
        ;;
esac

print_success "Korean Learning System operation completed! 🎯"