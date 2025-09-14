#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the simplified Korean reading comprehension system
Only topic questions, random task selection
"""

import requests
import json

BASE_URL = "http://localhost:8080"

def test_simplified_system():
    """Test the simplified system with only topic questions"""
    print("🔍 Testing simplified Korean reading comprehension system...")

    # Test multiple task retrievals to verify randomization
    print("\n📚 Testing random task selection...")
    task_ids = set()

    for i in range(5):
        response = requests.post(f"{BASE_URL}/api/get_task",
                               json={"source": "auto"})

        if response.status_code != 200:
            print(f"❌ Failed to get task {i+1}: {response.status_code}")
            continue

        task_data = response.json()
        if task_data.get("success"):
            task_id = task_data["task"].get("id", f"unknown_{i}")
            task_ids.add(task_id)
            print(f"   Task {i+1}: {task_id}")
        else:
            print(f"❌ Task {i+1} failed: {task_data}")

    if len(task_ids) > 1:
        print(f"✅ Random selection working! Got {len(task_ids)} different tasks")
    else:
        print(f"⚠️ Only got {len(task_ids)} unique task(s). May need more variety.")

    # Test topic question grading
    print("\n📝 Testing topic question grading...")

    # Get a fresh task
    response = requests.post(f"{BASE_URL}/api/get_task", json={"source": "auto"})
    if response.status_code != 200:
        print(f"❌ Failed to get task for grading test")
        return False

    task_data = response.json()
    if not task_data.get("success"):
        print(f"❌ Get task failed: {task_data}")
        return False

    task = task_data["task"]
    print(f"   Testing with task: {task.get('id', 'unknown')}")

    # Test various topic answers
    test_answers = [
        "이 글의 주제는 환경 보호와 도시 녹화의 중요성입니다.",
        "도시 녹화가 환경 문제 해결에 도움이 됩니다.",
        "글의 내용은 녹색 환경에 관한 것입니다.",
        "짧은답",  # Too short
        ""  # Empty
    ]

    for i, answer in enumerate(test_answers):
        print(f"\n   Testing answer {i+1}: '{answer[:50]}{'...' if len(answer) > 50 else ''}'")

        response = requests.post(f"{BASE_URL}/api/submit_answer", json={
            "task": task,
            "question_type": "topic",
            "answer": answer
        })

        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"      ✅ Score: {result.get('score', 0)}, Correct: {result.get('correct', False)}")
                print(f"      📝 Feedback: {result.get('feedback', 'No feedback')[:100]}...")
            else:
                print(f"      ❌ Grading failed: {result}")
        else:
            print(f"      ❌ Request failed: {response.status_code}")

    # Test error cases
    print("\n🧪 Testing error handling...")

    # Wrong question type
    response = requests.post(f"{BASE_URL}/api/submit_answer", json={
        "task": task,
        "question_type": "keywords",  # No longer supported
        "answer": "test"
    })

    if response.status_code == 200:
        result = response.json()
        print(f"   Wrong question type: {result.get('feedback', 'No feedback')}")

    # Missing parameters
    response = requests.post(f"{BASE_URL}/api/submit_answer", json={
        "task": task
        # Missing question_type and answer
    })

    print(f"   Missing params: Status {response.status_code}")

    print("\n✅ Simplified system testing completed!")
    return True

if __name__ == "__main__":
    success = test_simplified_system()
    exit(0 if success else 1)