#!/bin/bash

# 한국어 학습 시스템 Docker 배포 스크립트
# 로컬 및 온라인 도커 환경 지원

set -e

echo "🚀 한국어 학습 시스템 Docker 배포 시작"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수 정의
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Docker 설치 확인
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker가 설치되지 않았습니다. Docker를 먼저 설치해주세요."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose가 설치되지 않았습니다. Docker Compose를 먼저 설치해주세요."
        exit 1
    fi
    
    print_status "Docker 환경 확인 완료"
}

# 필요한 디렉토리 생성
create_directories() {
    print_info "필요한 디렉토리 생성 중..."
    mkdir -p logs
    mkdir -p data/enhanced_tasks
    mkdir -p data/legacy_tasks
    print_status "디렉토리 생성 완료"
}

# Docker 이미지 빌드
build_image() {
    print_info "Docker 이미지 빌드 중... (시간이 오래 걸릴 수 있습니다)"
    docker-compose build
    print_status "Docker 이미지 빌드 완료"
}

# 컨테이너 실행
start_containers() {
    print_info "Docker 컨테이너 실행 중..."
    docker-compose up -d
    print_status "컨테이너 실행 완료"
    
    print_info "헬스체크 대기 중..."
    sleep 30
    
    # 헬스체크 확인
    if curl -f http://localhost:8080/api/status &>/dev/null; then
        print_status "시스템 헬스체크 성공!"
    else
        print_warning "헬스체크에 실패했습니다. 컨테이너 로그를 확인해보세요."
    fi
}

# 컨테이너 중지
stop_containers() {
    print_info "Docker 컨테이너 중지 중..."
    docker-compose down
    print_status "컨테이너 중지 완료"
}

# 로그 확인
show_logs() {
    print_info "컨테이너 로그 확인 중..."
    docker-compose logs -f korean-learning-system
}

# 시스템 상태 확인
check_status() {
    print_info "시스템 상태 확인 중..."
    docker-compose ps
    
    print_info "컨테이너 상태:"
    if docker ps | grep -q korean-learning-app; then
        print_status "한국어 학습 시스템: 실행 중"
    else
        print_error "한국어 학습 시스템: 중지됨"
    fi
    
    if docker ps | grep -q korean-learning-redis; then
        print_status "Redis 캐시: 실행 중"
    else
        print_error "Redis 캐시: 중지됨"
    fi
}

# 전체 재배포
redeploy() {
    print_info "전체 시스템 재배포 중..."
    stop_containers
    build_image
    start_containers
    print_status "재배포 완료"
}

# 사용법 출력
show_usage() {
    echo "한국어 학습 시스템 Docker 배포 스크립트"
    echo ""
    echo "사용법: $0 [명령어]"
    echo ""
    echo "명령어:"
    echo "  build     - Docker 이미지만 빌드"
    echo "  start     - 컨테이너 시작 (빌드 포함)"
    echo "  stop      - 컨테이너 중지"
    echo "  restart   - 컨테이너 재시작"
    echo "  logs      - 실시간 로그 확인"
    echo "  status    - 시스템 상태 확인"
    echo "  redeploy  - 전체 재배포"
    echo "  help      - 이 도움말 출력"
    echo ""
    echo "예시:"
    echo "  $0 start    # 시스템 시작"
    echo "  $0 logs     # 로그 실시간 확인"
    echo "  $0 status   # 상태 확인"
}

# 메인 실행 로직
main() {
    case "${1:-start}" in
        build)
            check_docker
            create_directories
            build_image
            ;;
        start)
            check_docker
            create_directories
            build_image
            start_containers
            print_status "🎉 한국어 학습 시스템이 성공적으로 시작되었습니다!"
            print_info "📱 웹 브라우저에서 http://localhost:8080 으로 접속하세요"
            ;;
        stop)
            stop_containers
            ;;
        restart)
            stop_containers
            start_containers
            ;;
        logs)
            show_logs
            ;;
        status)
            check_status
            ;;
        redeploy)
            redeploy
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_error "알 수 없는 명령어: $1"
            show_usage
            exit 1
            ;;
    esac
}

# 스크립트 실행
main "$@"