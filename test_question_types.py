#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test all three question types with the new grading system
"""

import requests
import json

BASE_URL = "http://localhost:8080"

def test_all_question_types():
    """Test all three question types to verify grading fixes"""
    print("🔍 Testing all question types with new grading system...")

    # First, get a task
    response = requests.post(f"{BASE_URL}/api/get_task",
                           json={"source": "auto"})

    if response.status_code != 200:
        print(f"❌ Failed to get task: {response.status_code}")
        return False

    task_data = response.json()
    if not task_data.get("success"):
        print(f"❌ Get task failed: {task_data}")
        return False

    task = task_data["task"]
    print(f"✅ Got task: {task.get('id', 'unknown')}")
    print(f"   Keywords: {task.get('keywords', [])}")
    print(f"   Sentences: {len(task.get('sentences', []))} sentences")

    # Test Question 1: Keywords MCQ
    print("\n📝 Testing Question 1: Keywords MCQ")
    keywords_response = requests.post(f"{BASE_URL}/api/submit_answer", json={
        "task": task,
        "question_type": "keywords",
        "answer": 0  # First keyword choice
    })

    print(f"   Status: {keywords_response.status_code}")
    if keywords_response.status_code == 200:
        result = keywords_response.json()
        print(f"   Result: correct={result.get('correct')}, score={result.get('score')}")
        print(f"   Feedback: {result.get('feedback')}")
    else:
        print(f"   Error: {keywords_response.text}")

    # Test Question 2: Center Sentence MCQ
    print("\n📝 Testing Question 2: Center Sentence MCQ")
    center_response = requests.post(f"{BASE_URL}/api/submit_answer", json={
        "task": task,
        "question_type": "center",
        "answer": 0  # First sentence choice
    })

    print(f"   Status: {center_response.status_code}")
    if center_response.status_code == 200:
        result = center_response.json()
        print(f"   Result: correct={result.get('correct')}, score={result.get('score')}")
        print(f"   Feedback: {result.get('feedback')}")
    else:
        print(f"   Error: {center_response.text}")

    # Test Question 3: Topic Free Response
    print("\n📝 Testing Question 3: Topic Free Response")
    topic_response = requests.post(f"{BASE_URL}/api/submit_answer", json={
        "task": task,
        "question_type": "topic",
        "answer": "이 문단의 주제는 환경 보호와 도시 녹화의 중요성입니다."
    })

    print(f"   Status: {topic_response.status_code}")
    if topic_response.status_code == 200:
        result = topic_response.json()
        print(f"   Result: correct={result.get('correct')}, score={result.get('score')}")
        print(f"   Feedback: {result.get('feedback')}")
    else:
        print(f"   Error: {topic_response.text}")

    # Test error cases
    print("\n🧪 Testing Error Cases")

    # Wrong answer type for keywords (should be int, sending string)
    error_response1 = requests.post(f"{BASE_URL}/api/submit_answer", json={
        "task": task,
        "question_type": "keywords",
        "answer": "wrong type"
    })
    print(f"   Keywords with string: {error_response1.status_code}")

    # Wrong answer type for topic (should be string, sending int)
    error_response2 = requests.post(f"{BASE_URL}/api/submit_answer", json={
        "task": task,
        "question_type": "topic",
        "answer": 123
    })
    print(f"   Topic with int: {error_response2.status_code}")

    # Unknown question type
    error_response3 = requests.post(f"{BASE_URL}/api/submit_answer", json={
        "task": task,
        "question_type": "unknown",
        "answer": 0
    })
    print(f"   Unknown type: {error_response3.status_code}")

    print("\n✅ All tests completed!")
    return True

if __name__ == "__main__":
    success = test_all_question_types()
    exit(0 if success else 1)