#!/usr/bin/env python3
"""
System Integration Script
완전한 독해 문제 생성 및 평가 시스템 통합 관리
"""

import subprocess
import time
import json
import requests
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemIntegration:
    """시스템 통합 관리자"""
    
    def __init__(self):
        self.services = {
            # 기본 인프라 서비스
            "postgres": {"port": 5432, "health": None},
            "redis": {"port": 6379, "health": None},
            
            # 생성 시스템
            "generator": {"port": None, "health": None},
            "parallel_generator": {"port": None, "health": None},
            
            # 평가 시스템  
            "quality-evaluator": {"port": None, "health": None},
            "quality-interface": {"port": 5002, "health": "/health"},
            
            # 퀴즈 시스템
            "quiz-api": {"port": 5001, "health": "/api/health"},
            
            # 웹 인터페이스
            "web-interface": {"port": 5000, "health": "/health"}
        }
        
        self.integration_status = {
            "system_ready": False,
            "data_pipeline_ready": False,
            "quality_system_ready": False,
            "quiz_system_ready": False,
            "api_endpoints_ready": False
        }
    
    def check_service_health(self, service_name: str) -> bool:
        """서비스 헬스 체크"""
        service = self.services.get(service_name)
        if not service or not service.get("port") or not service.get("health"):
            return False
            
        try:
            url = f"http://localhost:{service['port']}{service['health']}"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def wait_for_service(self, service_name: str, timeout: int = 60) -> bool:
        """서비스가 준비될 때까지 대기"""
        logger.info(f"Waiting for {service_name} to be ready...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.check_service_health(service_name):
                logger.info(f"✅ {service_name} is ready")
                return True
            time.sleep(5)
        
        logger.error(f"❌ {service_name} failed to start within {timeout} seconds")
        return False
    
    def start_services(self, services: List[str] = None) -> bool:
        """서비스 시작"""
        if services is None:
            services = ["quiz-api", "quality-interface"]
        
        logger.info("Starting system integration services...")
        
        try:
            # Docker Compose로 서비스 시작
            cmd = ["docker-compose", "-f", "docker-compose.yml", "-f", "docker-compose.quiz.yml", "up", "-d"] + services
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to start services: {result.stderr}")
                return False
            
            # 서비스 준비 대기
            all_ready = True
            for service in services:
                if not self.wait_for_service(service):
                    all_ready = False
            
            return all_ready
            
        except Exception as e:
            logger.error(f"Error starting services: {e}")
            return False
    
    def stop_services(self, services: List[str] = None) -> bool:
        """서비스 중지"""
        if services is None:
            services = ["quiz-api", "quality-interface", "quality-processor"]
        
        logger.info("Stopping integration services...")
        
        try:
            cmd = ["docker-compose", "-f", "docker-compose.yml", "-f", "docker-compose.quiz.yml", "stop"] + services
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Services stopped successfully")
                return True
            else:
                logger.error(f"Failed to stop services: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error stopping services: {e}")
            return False
    
    def check_data_pipeline(self) -> bool:
        """데이터 파이프라인 상태 확인"""
        try:
            # 생성된 JSON 파일 수 확인
            out_dir = Path("generator/out")
            if not out_dir.exists():
                logger.warning("Output directory not found")
                return False
            
            json_files = list(out_dir.glob("*.json"))
            logger.info(f"Found {len(json_files)} JSON files in output directory")
            
            # 품질 평가 보고서 확인
            reports_dir = Path("generator/test_reports")
            if reports_dir.exists():
                report_files = list(reports_dir.glob("quality_*.json"))
                logger.info(f"Found {len(report_files)} quality reports")
            
            self.integration_status["data_pipeline_ready"] = len(json_files) > 0
            return self.integration_status["data_pipeline_ready"]
            
        except Exception as e:
            logger.error(f"Error checking data pipeline: {e}")
            return False
    
    def test_quiz_api(self) -> bool:
        """퀴즈 API 기능 테스트"""
        try:
            base_url = "http://localhost:5001/api"
            
            # 헬스 체크
            response = requests.get(f"{base_url}/health")
            if response.status_code != 200:
                logger.error("Quiz API health check failed")
                return False
            
            # 메타데이터 조회
            response = requests.get(f"{base_url}/meta/difficulty-levels")
            if response.status_code != 200:
                logger.error("Failed to get metadata")
                return False
            
            # 퀴즈 생성 테스트
            quiz_data = {
                "count": 3,
                "difficulty": "medium",
                "quiz_type": "mixed",
                "min_quality_score": 50.0
            }
            
            response = requests.post(f"{base_url}/quiz/generate", json=quiz_data)
            if response.status_code == 200:
                result = response.json()
                if result.get("success") and len(result.get("data", {}).get("questions", [])) > 0:
                    logger.info("✅ Quiz API test passed")
                    return True
            
            logger.error("Quiz generation test failed")
            return False
            
        except Exception as e:
            logger.error(f"Error testing quiz API: {e}")
            return False
    
    def test_student_profiles(self) -> bool:
        """학생 프로필 시스템 테스트"""
        try:
            base_url = "http://localhost:5001/api"
            
            # 테스트 학생 생성
            student_data = {
                "student_id": "test_integration_001",
                "name": "통합테스트학생",
                "grade_level": 2,
                "school": "통합테스트고등학교",
                "reading_level": "중급",
                "preferences": {
                    "preferred_difficulty": "medium",
                    "preferred_topics": ["과학", "기술"],
                    "max_questions_per_session": 10
                }
            }
            
            # 학생 생성
            response = requests.post(f"{base_url}/student/profile", json=student_data)
            if response.status_code not in [200, 400]:  # 400은 이미 존재하는 경우
                logger.error("Failed to create test student")
                return False
            
            # 학생 조회
            response = requests.get(f"{base_url}/student/profile/test_integration_001")
            if response.status_code != 200:
                logger.error("Failed to retrieve student profile")
                return False
            
            profile = response.json()
            if profile.get("success") and profile.get("data", {}).get("name") == "통합테스트학생":
                logger.info("✅ Student profile system test passed")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error testing student profiles: {e}")
            return False
    
    def run_full_integration_test(self) -> Dict[str, bool]:
        """전체 통합 테스트 실행"""
        logger.info("🚀 Starting full system integration test...")
        
        test_results = {
            "services_started": False,
            "data_pipeline": False,
            "quiz_api": False,
            "student_profiles": False,
            "quality_interface": False
        }
        
        # 1. 서비스 시작
        test_results["services_started"] = self.start_services()
        if not test_results["services_started"]:
            logger.error("Failed to start services. Aborting integration test.")
            return test_results
        
        # 2. 데이터 파이프라인 확인
        test_results["data_pipeline"] = self.check_data_pipeline()
        
        # 3. 퀴즈 API 테스트
        test_results["quiz_api"] = self.test_quiz_api()
        
        # 4. 학생 프로필 테스트
        test_results["student_profiles"] = self.test_student_profiles()
        
        # 5. 품질 인터페이스 확인
        test_results["quality_interface"] = self.check_service_health("quality-interface")
        
        # 결과 출력
        logger.info("🔍 Integration Test Results:")
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {test_name}: {status}")
        
        # 전체 성공률 계산
        success_count = sum(test_results.values())
        success_rate = success_count / len(test_results) * 100
        
        logger.info(f"🎯 Overall Success Rate: {success_count}/{len(test_results)} ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            logger.info("🎉 System integration test PASSED!")
        else:
            logger.warning("⚠️  System integration test FAILED - Some components need attention")
        
        return test_results
    
    def get_system_status(self) -> Dict:
        """시스템 전체 상태 조회"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "data_stats": {},
            "integration_status": self.integration_status
        }
        
        # 서비스 상태 확인
        for service_name in self.services:
            status["services"][service_name] = {
                "healthy": self.check_service_health(service_name),
                "port": self.services[service_name].get("port")
            }
        
        # 데이터 통계
        try:
            out_dir = Path("generator/out")
            if out_dir.exists():
                status["data_stats"]["total_items"] = len(list(out_dir.glob("*.json")))
            
            reports_dir = Path("generator/test_reports")
            if reports_dir.exists():
                status["data_stats"]["quality_reports"] = len(list(reports_dir.glob("quality_*.json")))
        except Exception as e:
            logger.warning(f"Error collecting data stats: {e}")
        
        return status

def main():
    """메인 실행 함수"""
    integrator = SystemIntegration()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "start":
            services = sys.argv[2:] if len(sys.argv) > 2 else None
            success = integrator.start_services(services)
            sys.exit(0 if success else 1)
            
        elif command == "stop":
            services = sys.argv[2:] if len(sys.argv) > 2 else None
            success = integrator.stop_services(services)
            sys.exit(0 if success else 1)
            
        elif command == "test":
            test_results = integrator.run_full_integration_test()
            success = all(test_results.values())
            sys.exit(0 if success else 1)
            
        elif command == "status":
            status = integrator.get_system_status()
            print(json.dumps(status, indent=2, ensure_ascii=False))
            sys.exit(0)
            
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    
    else:
        print("Usage: python system_integration.py [start|stop|test|status] [services...]")
        print("Examples:")
        print("  python system_integration.py start")
        print("  python system_integration.py stop")
        print("  python system_integration.py test")
        print("  python system_integration.py status")
        sys.exit(1)

if __name__ == "__main__":
    main()