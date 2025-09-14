#!/bin/bash

# Korean Learning System - Docker Build Script
# This script builds Docker images for the Korean Learning System

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
BUILD_TARGET="${BUILD_TARGET:-production}"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-}"
DOCKER_TAG="${DOCKER_TAG:-latest}"
BUILD_ARGS=""
VERBOSE=false
CLEAN=false

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
Korean Learning System - Docker Build Script

Usage: $0 [OPTIONS]

Options:
    -t, --target TARGET     Build target (development|production) [default: production]
    -r, --registry REGISTRY Docker registry URL for pushing images
    -T, --tag TAG          Docker tag for images [default: latest]
    -c, --clean            Clean existing images before building
    -v, --verbose          Enable verbose output
    -h, --help             Show this help message

Examples:
    $0                                          # Build production images
    $0 --target development                     # Build development images
    $0 --tag v1.0.0 --registry myregistry.com  # Build and tag for registry
    $0 --clean --verbose                        # Clean build with verbose output

Environment Variables:
    BUILD_TARGET    Build target (development|production)
    DOCKER_REGISTRY Docker registry URL
    DOCKER_TAG      Docker image tag
    DOCKER_BUILDKIT Enable BuildKit (recommended)

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--target)
            BUILD_TARGET="$2"
            shift 2
            ;;
        -r|--registry)
            DOCKER_REGISTRY="$2"
            shift 2
            ;;
        -T|--tag)
            DOCKER_TAG="$2"
            shift 2
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate build target
if [[ ! "$BUILD_TARGET" =~ ^(development|production)$ ]]; then
    print_error "Invalid build target: $BUILD_TARGET (must be 'development' or 'production')"
    exit 1
fi

# Enable BuildKit for better performance
export DOCKER_BUILDKIT=1

print_status "Starting Korean Learning System Docker build..."
print_status "Build target: $BUILD_TARGET"
print_status "Docker tag: $DOCKER_TAG"
[[ -n "$DOCKER_REGISTRY" ]] && print_status "Registry: $DOCKER_REGISTRY"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running or not accessible"
    exit 1
fi

# Check required files
required_files=(
    "Dockerfile.flask"
    "requirements.txt"
    "docker-compose-complete.yml"
    ".env.docker"
)

for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        print_error "Required file missing: $file"
        exit 1
    fi
done

# Clean existing images if requested
if [[ "$CLEAN" == "true" ]]; then
    print_status "Cleaning existing Korean Learning System images..."
    docker images --format "table {{.Repository}}:{{.Tag}}" | grep korean-learning | while read -r image; do
        if [[ -n "$image" && "$image" != "REPOSITORY:TAG" ]]; then
            print_status "Removing image: $image"
            docker rmi "$image" || true
        fi
    done
    
    # Clean dangling images
    print_status "Removing dangling images..."
    docker image prune -f || true
fi

# Set image name
if [[ -n "$DOCKER_REGISTRY" ]]; then
    IMAGE_NAME="${DOCKER_REGISTRY}/korean-learning-system"
else
    IMAGE_NAME="korean-learning-system"
fi

FULL_IMAGE_NAME="${IMAGE_NAME}:${DOCKER_TAG}"

# Set build arguments
BUILD_ARGS="--target $BUILD_TARGET"

if [[ "$VERBOSE" == "true" ]]; then
    BUILD_ARGS="$BUILD_ARGS --progress=plain"
fi

# Add build metadata
BUILD_ARGS="$BUILD_ARGS --label org.opencontainers.image.created=$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
BUILD_ARGS="$BUILD_ARGS --label org.opencontainers.image.version=$DOCKER_TAG"
BUILD_ARGS="$BUILD_ARGS --label org.opencontainers.image.title=Korean Learning System"
BUILD_ARGS="$BUILD_ARGS --label org.opencontainers.image.description=Korean reading comprehension learning system with 4-phase methodology"

# Build the main Flask application image
print_status "Building Korean Learning System Flask application..."
print_status "Command: docker build $BUILD_ARGS -f Dockerfile.flask -t $FULL_IMAGE_NAME ."

if ! docker build $BUILD_ARGS -f Dockerfile.flask -t "$FULL_IMAGE_NAME" .; then
    print_error "Failed to build Flask application image"
    exit 1
fi

print_success "Successfully built Flask application image: $FULL_IMAGE_NAME"

# Tag additional versions
if [[ "$DOCKER_TAG" != "latest" ]]; then
    LATEST_IMAGE_NAME="${IMAGE_NAME}:latest"
    docker tag "$FULL_IMAGE_NAME" "$LATEST_IMAGE_NAME"
    print_status "Tagged as: $LATEST_IMAGE_NAME"
fi

# Build additional service images if they exist
additional_services=(
    "generator:./generator/Dockerfile"
    "grader:./grader/Dockerfile"
)

for service_config in "${additional_services[@]}"; do
    IFS=':' read -r service_name dockerfile_path <<< "$service_config"
    
    if [[ -f "$dockerfile_path" ]]; then
        service_image_name="${IMAGE_NAME}-${service_name}:${DOCKER_TAG}"
        print_status "Building $service_name service..."
        
        if docker build -f "$dockerfile_path" -t "$service_image_name" "./$(dirname "$dockerfile_path")"; then
            print_success "Successfully built $service_name image: $service_image_name"
        else
            print_warning "Failed to build $service_name image (continuing...)"
        fi
    fi
done

# Push to registry if specified
if [[ -n "$DOCKER_REGISTRY" ]]; then
    print_status "Pushing images to registry: $DOCKER_REGISTRY"
    
    if docker push "$FULL_IMAGE_NAME"; then
        print_success "Successfully pushed: $FULL_IMAGE_NAME"
    else
        print_error "Failed to push to registry"
        exit 1
    fi
    
    if [[ "$DOCKER_TAG" != "latest" ]]; then
        docker push "$LATEST_IMAGE_NAME" || print_warning "Failed to push latest tag"
    fi
fi

# Display build summary
print_success "Build completed successfully!"
echo
print_status "Built images:"
docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" | grep korean-learning

echo
print_status "To run the system:"
echo "  Development: docker-compose -f docker-compose-complete.yml --env-file .env.docker up"
echo "  Production:  docker-compose -f docker-compose-complete.yml --env-file .env.docker up -d"

echo
print_status "To test the deployment:"
echo "  ./run.sh --test"

print_success "Korean Learning System build completed successfully! 🚀"