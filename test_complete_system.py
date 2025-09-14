#!/usr/bin/env python3
"""
Complete System Test for 4-Phase Korean Summary Learning System
Tests all integrations and verifies the complete workflow.
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8080"

def test_system_status():
    """Test basic system status"""
    print("🧪 Testing System Status...")
    
    try:
        # Test home page
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        print("  ✅ Home page accessible")
        
        # Test API status
        response = requests.get(f"{BASE_URL}/api/status")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'running'
        print("  ✅ API status endpoint working")
        
        # Test learning system accessibility  
        response = requests.get(f"{BASE_URL}/learning")
        assert response.status_code == 200
        print("  ✅ Learning system accessible")
        
        return True
        
    except Exception as e:
        print(f"  ❌ System status test failed: {e}")
        return False

def test_task_loading():
    """Test enhanced task loading"""
    print("🧪 Testing Enhanced Task Loading...")
    
    try:
        response = requests.get(f"{BASE_URL}/learning/get_task")
        assert response.status_code == 200
        
        data = response.json()
        assert data['success'] == True
        assert 'task' in data
        
        task = data['task']
        required_fields = ['id', 'content', 'topic', 'difficulty', 'sentence_count']
        
        for field in required_fields:
            assert field in task, f"Missing required field: {field}"
        
        print(f"  ✅ Task loaded successfully: {task['id']}")
        print(f"  📊 Content length: {len(task['content'])} chars")
        print(f"  🎯 Topic: {task['topic']}")
        print(f"  📈 Difficulty: {task['difficulty']}")
        print(f"  📝 Sentences: {task['sentence_count']}")
        
        return task
        
    except Exception as e:
        print(f"  ❌ Task loading test failed: {e}")
        return None

def test_phase_progression(task):
    """Test all 4 phases of learning"""
    print("🧪 Testing 4-Phase Learning Progression...")
    
    if not task:
        print("  ❌ No task available for testing")
        return False
    
    session = requests.Session()
    
    try:
        # Get task first to establish session
        response = session.get(f"{BASE_URL}/learning/get_task")
        assert response.status_code == 200
        
        phases_tested = []
        
        # Test Phase 1: Component Identification
        print("  🔍 Testing Phase 1: Component Identification...")
        response = session.get(f"{BASE_URL}/learning/start_phase/1")
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                phase_data = data['phase_data']
                assert 'objective' in phase_data
                assert 'target_sentence' in phase_data
                print("    ✅ Phase 1 initialization successful")
                phases_tested.append(1)
            else:
                print(f"    ❌ Phase 1 failed: {data.get('message', 'Unknown error')}")
        else:
            print(f"    ❌ Phase 1 request failed: {response.status_code}")
        
        # Test Phase 2: Necessity Judgment
        print("  ⚖️ Testing Phase 2: Necessity Judgment...")
        response = session.get(f"{BASE_URL}/learning/start_phase/2")
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                phase_data = data['phase_data']
                assert 'objective' in phase_data
                print("    ✅ Phase 2 initialization successful")
                phases_tested.append(2)
            else:
                print(f"    ❌ Phase 2 failed: {data.get('message', 'Unknown error')}")
        else:
            print(f"    ❌ Phase 2 request failed: {response.status_code}")
        
        # Test Phase 3: Generalization
        print("  🔄 Testing Phase 3: Generalization...")
        response = session.get(f"{BASE_URL}/learning/start_phase/3")
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                phase_data = data['phase_data']
                assert 'objective' in phase_data
                print("    ✅ Phase 3 initialization successful")
                phases_tested.append(3)
            else:
                print(f"    ❌ Phase 3 failed: {data.get('message', 'Unknown error')}")
        else:
            print(f"    ❌ Phase 3 request failed: {response.status_code}")
        
        # Test Phase 4: Theme Reconstruction
        print("  🎨 Testing Phase 4: Theme Reconstruction...")
        response = session.get(f"{BASE_URL}/learning/start_phase/4")
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                phase_data = data['phase_data']
                assert 'objective' in phase_data
                print("    ✅ Phase 4 initialization successful")
                phases_tested.append(4)
            else:
                print(f"    ❌ Phase 4 failed: {data.get('message', 'Unknown error')}")
        else:
            print(f"    ❌ Phase 4 request failed: {response.status_code}")
        
        print(f"  📊 Successfully tested phases: {phases_tested}")
        return len(phases_tested) == 4
        
    except Exception as e:
        print(f"  ❌ Phase progression test failed: {e}")
        return False

def test_answer_submission():
    """Test answer submission functionality"""
    print("🧪 Testing Answer Submission...")
    
    session = requests.Session()
    
    try:
        # Get a task to work with
        response = session.get(f"{BASE_URL}/learning/get_task")
        assert response.status_code == 200
        
        # Start Phase 1
        response = session.get(f"{BASE_URL}/learning/start_phase/1")
        assert response.status_code == 200
        
        # Test Phase 1 submission with sample data
        sample_phase1_data = {
            "response_data": {
                "sentence_id": 1,
                "identified_components": {
                    "주어": ["언어는"],
                    "서술어": ["하는", "힘이다"],
                    "목적어": ["도구를"]
                }
            }
        }
        
        response = session.post(
            f"{BASE_URL}/learning/submit_phase/1",
            json=sample_phase1_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                evaluation = data['evaluation']
                assert 'score' in evaluation
                assert 'mastery_achieved' in evaluation
                print("    ✅ Phase 1 submission successful")
                print(f"    📊 Score: {evaluation['score']:.2f}")
                return True
            else:
                print(f"    ❌ Phase 1 submission failed: {data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"    ❌ Phase 1 submission request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Answer submission test failed: {e}")
        return False

def test_progress_tracking():
    """Test progress tracking functionality"""
    print("🧪 Testing Progress Tracking...")
    
    session = requests.Session()
    
    try:
        # Get a task to establish session
        response = session.get(f"{BASE_URL}/learning/get_task")
        assert response.status_code == 200
        
        # Test progress endpoint
        response = session.get(f"{BASE_URL}/learning/get_progress")
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                progress = data['progress']
                print("    ✅ Progress tracking working")
                print(f"    📈 Current progress: {json.dumps(progress, indent=2, ensure_ascii=False)}")
                return True
            else:
                print(f"    ❌ Progress tracking failed: {data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"    ❌ Progress request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Progress tracking test failed: {e}")
        return False

def run_complete_system_test():
    """Run complete system test suite"""
    print("🚀 4단계 한국어 요약 학습 시스템 - 완전 통합 테스트")
    print("=" * 80)
    
    test_results = []
    
    # Wait for server to start
    print("⏳ Waiting for server to be ready...")
    time.sleep(3)
    
    # Run all tests
    test_results.append(("System Status", test_system_status()))
    
    task = test_task_loading()
    test_results.append(("Task Loading", task is not None))
    
    test_results.append(("Phase Progression", test_phase_progression(task)))
    test_results.append(("Answer Submission", test_answer_submission()))
    test_results.append(("Progress Tracking", test_progress_tracking()))
    
    # Print results
    print("\n" + "=" * 80)
    print("📋 테스트 결과 요약")
    print("=" * 80)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1
    
    print(f"\n📊 전체 결과: {passed}/{total} 테스트 통과 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 모든 테스트 통과! 시스템이 완전히 작동합니다.")
        print(f"🌐 시스템 접속: {BASE_URL}")
        print(f"🎯 4단계 학습 시스템: {BASE_URL}/learning")
        print(f"📝 레거시 퀴즈: {BASE_URL}/legacy")
        return True
    else:
        print("⚠️ 일부 테스트 실패. 로그를 확인해주세요.")
        return False

if __name__ == "__main__":
    success = run_complete_system_test()
    exit(0 if success else 1)