#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Contract Test for Korean Reading Comprehension System
Tests the new /api/get_task and /api/submit_answer endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8080"

def test_get_task_contract():
    """Test /api/get_task endpoint contract"""
    print("🔍 Testing /api/get_task endpoint...")

    response = requests.post(f"{BASE_URL}/api/get_task",
                           json={"source": "auto"})

    print(f"Status Code: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    print(f"Response keys: {list(data.keys())}")

    # Contract verification
    assert data["success"] is True, "Response should have success=True"
    assert "task" in data, "Response should contain 'task' field"
    assert isinstance(data["task"], dict), "Task should be a dictionary"

    task = data["task"]

    # Basic task structure validation
    required_fields = ["id"]
    for field in required_fields:
        assert field in task, f"Task should contain '{field}' field"

    print("✅ /api/get_task contract test passed!")
    return task

def test_submit_answer_contract(task):
    """Test /api/submit_answer endpoint contract"""
    print("🔍 Testing /api/submit_answer endpoint...")

    response = requests.post(f"{BASE_URL}/api/submit_answer",
                           json={"task": task, "answer_index": 0})

    print(f"Status Code: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    print(f"Response keys: {list(data.keys())}")

    # Contract verification
    assert data["success"] is True, "Response should have success=True"
    assert "correct" in data, "Response should contain 'correct' field"
    assert "feedback" in data, "Response should contain 'feedback' field"
    assert isinstance(data["correct"], bool), "Correct should be boolean"
    assert isinstance(data["feedback"], str), "Feedback should be string"

    print(f"Grading result: correct={data['correct']}, feedback='{data['feedback'][:50]}...'")
    print("✅ /api/submit_answer contract test passed!")

def test_error_handling():
    """Test error handling"""
    print("🔍 Testing error handling...")

    # Test submit_answer with missing data
    response = requests.post(f"{BASE_URL}/api/submit_answer", json={})
    assert response.status_code == 400, "Should return 400 for missing data"

    data = response.json()
    assert data["success"] is False, "Error response should have success=False"
    assert "error" in data, "Error response should contain 'error' field"

    print("✅ Error handling test passed!")

def main():
    """Run all contract tests"""
    print("🚀 Starting API Contract Tests")
    print("=" * 50)

    try:
        # Test 1: Get task
        task = test_get_task_contract()
        print()

        # Test 2: Submit answer
        test_submit_answer_contract(task)
        print()

        # Test 3: Error handling
        test_error_handling()
        print()

        print("🎉 All API contract tests passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)