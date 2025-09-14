#!/bin/bash
# Production Build Script for Korean Reading Comprehension System
# Builds optimized Docker images for production deployment

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
IMAGE_NAME="korean-reading-system"
REGISTRY="${DOCKER_REGISTRY:-}"
VERSION="${APP_VERSION:-latest}"
ENVIRONMENT="${ENVIRONMENT:-production}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_warning "docker-compose not found, checking for 'docker compose'"
        if ! docker compose version &> /dev/null; then
            log_error "Docker Compose is not available"
            exit 1
        fi
        DOCKER_COMPOSE="docker compose"
    else
        DOCKER_COMPOSE="docker-compose"
    fi
    
    # Check if we're in the project directory
    if [[ ! -f "$PROJECT_DIR/Dockerfile.production" ]]; then
        log_error "Dockerfile.production not found. Are you in the correct directory?"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Clean up old images and containers
cleanup_old_resources() {
    log_info "Cleaning up old resources..."
    
    # Remove old containers
    if docker ps -a --filter "label=com.koreanreading.environment=$ENVIRONMENT" --format "{{.ID}}" | grep -q .; then
        log_info "Removing old containers..."
        docker ps -a --filter "label=com.koreanreading.environment=$ENVIRONMENT" --format "{{.ID}}" | xargs docker rm -f || true
    fi
    
    # Remove dangling images
    if docker images --filter "dangling=true" --format "{{.ID}}" | grep -q .; then
        log_info "Removing dangling images..."
        docker images --filter "dangling=true" --format "{{.ID}}" | xargs docker rmi -f || true
    fi
    
    # Prune build cache (keep last 24 hours)
    docker builder prune --filter "until=24h" -f || true
    
    log_success "Cleanup completed"
}

# Build production image
build_production_image() {
    log_info "Building production image..."
    
    cd "$PROJECT_DIR"
    
    # Build arguments
    BUILD_ARGS=(
        --build-arg "BUILDKIT_INLINE_CACHE=1"
        --build-arg "APP_VERSION=$VERSION"
        --build-arg "BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
        --build-arg "VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
    )
    
    # Labels
    LABELS=(
        --label "com.koreanreading.environment=$ENVIRONMENT"
        --label "com.koreanreading.version=$VERSION"
        --label "com.koreanreading.build-date=$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    )
    
    # Determine full image name
    if [[ -n "$REGISTRY" ]]; then
        FULL_IMAGE_NAME="$REGISTRY/$IMAGE_NAME:$VERSION"
        LATEST_IMAGE_NAME="$REGISTRY/$IMAGE_NAME:latest"
    else
        FULL_IMAGE_NAME="$IMAGE_NAME:$VERSION"
        LATEST_IMAGE_NAME="$IMAGE_NAME:latest"
    fi
    
    # Build production image
    log_info "Building image: $FULL_IMAGE_NAME"
    docker build \
        -f Dockerfile.production \
        --target production \
        --tag "$FULL_IMAGE_NAME" \
        --tag "$LATEST_IMAGE_NAME" \
        "${BUILD_ARGS[@]}" \
        "${LABELS[@]}" \
        --cache-from "$FULL_IMAGE_NAME" \
        .
    
    log_success "Production image built successfully"
    
    # Build development image if requested
    if [[ "${BUILD_DEV:-false}" == "true" ]]; then
        log_info "Building development image..."
        docker build \
            -f Dockerfile.production \
            --target development \
            --tag "$IMAGE_NAME:dev-$VERSION" \
            --tag "$IMAGE_NAME:dev-latest" \
            "${BUILD_ARGS[@]}" \
            "${LABELS[@]}" \
            .
        log_success "Development image built successfully"
    fi
    
    # Build testing image if requested
    if [[ "${BUILD_TEST:-false}" == "true" ]]; then
        log_info "Building testing image..."
        docker build \
            -f Dockerfile.production \
            --target testing \
            --tag "$IMAGE_NAME:test-$VERSION" \
            --tag "$IMAGE_NAME:test-latest" \
            "${BUILD_ARGS[@]}" \
            "${LABELS[@]}" \
            .
        log_success "Testing image built successfully"
    fi
}

# Verify image functionality
verify_image() {
    log_info "Verifying image functionality..."
    
    # Test basic image functionality
    log_info "Testing basic Python imports..."
    docker run --rm "$FULL_IMAGE_NAME" python -c "
import sys
print('Python version:', sys.version)

# Test critical imports
try:
    import flask
    import psycopg2
    import redis
    import konlpy
    import nltk
    print('✓ All critical imports successful')
except ImportError as e:
    print('✗ Import failed:', e)
    sys.exit(1)
"
    
    # Test Korean NLP functionality
    log_info "Testing Korean NLP functionality..."
    docker run --rm "$FULL_IMAGE_NAME" python -c "
try:
    from konlpy.tag import Mecab
    mecab = Mecab()
    result = mecab.morphs('한국어 테스트 문장입니다')
    print('✓ Korean NLP test successful:', result)
except Exception as e:
    print('✗ Korean NLP test failed:', e)
    import sys
    sys.exit(1)
"
    
    # Test application startup (dry run)
    log_info "Testing application startup..."
    docker run --rm -e "DRY_RUN=true" "$FULL_IMAGE_NAME" python -c "
try:
    from config.config import get_config
    config = get_config()
    print('✓ Configuration loaded successfully')
    print('Environment:', config.environment)
except Exception as e:
    print('✗ Configuration test failed:', e)
    import sys
    sys.exit(1)
"
    
    log_success "Image verification completed successfully"
}

# Show image information
show_image_info() {
    log_info "Image information:"
    
    # Image size
    IMAGE_SIZE=$(docker images --format "table {{.Size}}" "$FULL_IMAGE_NAME" | tail -n 1)
    echo "  Size: $IMAGE_SIZE"
    
    # Image layers
    LAYER_COUNT=$(docker history "$FULL_IMAGE_NAME" --format "{{.ID}}" | wc -l)
    echo "  Layers: $LAYER_COUNT"
    
    # Image labels
    echo "  Labels:"
    docker inspect "$FULL_IMAGE_NAME" --format '{{range $k, $v := .Config.Labels}}    {{$k}}: {{$v}}{{"\n"}}{{end}}'
    
    # Security scan if trivy is available
    if command -v trivy &> /dev/null; then
        log_info "Running security scan..."
        trivy image --severity HIGH,CRITICAL "$FULL_IMAGE_NAME" || log_warning "Security scan found issues"
    else
        log_warning "Trivy not found, skipping security scan"
    fi
}

# Push to registry if configured
push_to_registry() {
    if [[ -n "$REGISTRY" ]] && [[ "${PUSH_TO_REGISTRY:-false}" == "true" ]]; then
        log_info "Pushing to registry: $REGISTRY"
        
        # Login to registry if credentials are available
        if [[ -n "${REGISTRY_USERNAME:-}" ]] && [[ -n "${REGISTRY_PASSWORD:-}" ]]; then
            echo "$REGISTRY_PASSWORD" | docker login "$REGISTRY" -u "$REGISTRY_USERNAME" --password-stdin
        fi
        
        # Push images
        docker push "$FULL_IMAGE_NAME"
        docker push "$LATEST_IMAGE_NAME"
        
        # Push additional variants if built
        if [[ "${BUILD_DEV:-false}" == "true" ]]; then
            docker push "$REGISTRY/$IMAGE_NAME:dev-$VERSION"
            docker push "$REGISTRY/$IMAGE_NAME:dev-latest"
        fi
        
        if [[ "${BUILD_TEST:-false}" == "true" ]]; then
            docker push "$REGISTRY/$IMAGE_NAME:test-$VERSION"
            docker push "$REGISTRY/$IMAGE_NAME:test-latest"
        fi
        
        log_success "Images pushed to registry successfully"
    else
        log_info "Skipping registry push (not configured or disabled)"
    fi
}

# Save image to tar file
save_image() {
    if [[ "${SAVE_IMAGE:-false}" == "true" ]]; then
        OUTPUT_DIR="${IMAGE_OUTPUT_DIR:-./images}"
        mkdir -p "$OUTPUT_DIR"
        
        log_info "Saving image to tar file..."
        docker save "$FULL_IMAGE_NAME" | gzip > "$OUTPUT_DIR/${IMAGE_NAME}-${VERSION}.tar.gz"
        
        log_success "Image saved to $OUTPUT_DIR/${IMAGE_NAME}-${VERSION}.tar.gz"
    fi
}

# Generate deployment artifacts
generate_deployment_artifacts() {
    if [[ "${GENERATE_ARTIFACTS:-false}" == "true" ]]; then
        ARTIFACTS_DIR="${ARTIFACTS_OUTPUT_DIR:-./artifacts}"
        mkdir -p "$ARTIFACTS_DIR"
        
        log_info "Generating deployment artifacts..."
        
        # Generate docker-compose file with current image
        sed "s|image: korean-reading-system:production|image: $FULL_IMAGE_NAME|g" \
            docker-compose.production.yml > "$ARTIFACTS_DIR/docker-compose.yml"
        
        # Generate Kubernetes manifests if requested
        if [[ "${GENERATE_K8S:-false}" == "true" ]] && command -v kompose &> /dev/null; then
            cd "$ARTIFACTS_DIR"
            kompose convert -f docker-compose.yml
            cd "$PROJECT_DIR"
            log_success "Kubernetes manifests generated"
        fi
        
        # Copy configuration files
        cp -r config "$ARTIFACTS_DIR/"
        cp README.docker.md "$ARTIFACTS_DIR/"
        cp TROUBLESHOOTING.md "$ARTIFACTS_DIR/"
        
        log_success "Deployment artifacts generated in $ARTIFACTS_DIR"
    fi
}

# Main execution
main() {
    log_info "Starting production build process..."
    log_info "Image: $IMAGE_NAME:$VERSION"
    log_info "Environment: $ENVIRONMENT"
    
    # Execute build steps
    check_prerequisites
    cleanup_old_resources
    build_production_image
    verify_image
    show_image_info
    push_to_registry
    save_image
    generate_deployment_artifacts
    
    log_success "Production build completed successfully!"
    log_info "Image: $FULL_IMAGE_NAME"
    
    # Show next steps
    echo ""
    log_info "Next steps:"
    echo "  1. Test the image: docker run --rm -p 8000:8000 $FULL_IMAGE_NAME"
    echo "  2. Deploy using: docker-compose -f docker-compose.production.yml up -d"
    echo "  3. Check health: curl http://localhost/health"
}

# Handle script arguments
case "${1:-build}" in
    "build")
        main
        ;;
    "clean")
        cleanup_old_resources
        ;;
    "verify")
        verify_image
        ;;
    "info")
        show_image_info
        ;;
    "push")
        PUSH_TO_REGISTRY=true
        push_to_registry
        ;;
    *)
        echo "Usage: $0 [build|clean|verify|info|push]"
        echo ""
        echo "Commands:"
        echo "  build   - Build production image (default)"
        echo "  clean   - Clean up old resources"
        echo "  verify  - Verify existing image"
        echo "  info    - Show image information"
        echo "  push    - Push to registry"
        echo ""
        echo "Environment variables:"
        echo "  APP_VERSION     - Image version tag (default: latest)"
        echo "  DOCKER_REGISTRY - Registry URL for pushing"
        echo "  BUILD_DEV       - Build development variant (true/false)"
        echo "  BUILD_TEST      - Build testing variant (true/false)"
        echo "  PUSH_TO_REGISTRY - Push to registry (true/false)"
        echo "  SAVE_IMAGE      - Save image to tar file (true/false)"
        exit 1
        ;;
esac