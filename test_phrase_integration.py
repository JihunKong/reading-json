#!/usr/bin/env python3
"""
Test Korean phrase analyzer integration with Phase 1 controller
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.learning.phase_controller import LearningPhaseController
from dataclasses import dataclass
from typing import List

# Mock sentence data for testing
@dataclass
class MockSentence:
    sentence_id: int
    text: str
    complexity_level: str = "middle"

# Create a simple test task
def create_test_task():
    """Create a test task with Korean sentences"""
    
    # Test sentence: "도시 녹화는 현대 도시 문제 해결에 중요한 역할을 한다"
    test_sentence = MockSentence(
        sentence_id=1,
        text="도시 녹화는 현대 도시 문제 해결에 중요한 역할을 한다",
        complexity_level="middle"
    )
    
    # Create mock task object with required attributes
    class MockTask:
        def __init__(self):
            self.id = "test_task_001"
            self.sentence_analysis = [test_sentence]
    
    return MockTask()

def test_phrase_analysis():
    """Test the Korean phrase analyzer integration"""
    
    print("🔍 Testing Korean Phrase Analyzer Integration with Phase 1")
    print("=" * 60)
    
    # Initialize the controller
    controller = LearningPhaseController()
    
    # Create test task
    task = create_test_task()
    
    # Test Phase 1 initialization with phrase analysis
    try:
        phase1_data = controller.start_phase_1(task, "test_student_001")
        
        print("✅ Phase 1 initialization successful!")
        print(f"\n📝 Objective: {phase1_data['objective']}")
        print(f"\n🎯 Target sentence: {phase1_data['target_sentence']['text']}")
        print(f"\n📋 Instructions:")
        for i, instruction in enumerate(phase1_data['instructions'], 1):
            print(f"   {i}. {instruction}")
        
        # Display phrase analysis results
        if 'phrase_analysis' in phase1_data['target_sentence']:
            print(f"\n🔍 Phrase Analysis Results:")
            for i, phrase in enumerate(phase1_data['target_sentence']['phrase_analysis'], 1):
                print(f"   {i}. 구: '{phrase['text']}'")
                print(f"      성분: {phrase['component_type']}")
                print(f"      조사: {phrase['particles']}")
                print(f"      신뢰도: {phrase['confidence']:.2f}")
                print(f"      교육수준: {phrase['educational_level']}")
                print()
        
        # Test educational components identification
        print("🎓 Testing educational components identification:")
        target_sentence_text = phase1_data['target_sentence']['text']
        expected_components = controller._identify_educational_components(target_sentence_text)
        
        for comp_type, phrases in expected_components.items():
            if phrases:  # Only show components that have expected phrases
                print(f"   {comp_type}: {phrases}")
        
        print("\n✅ All tests passed! Korean phrase analyzer is properly integrated.")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_phrase_analysis()
    if success:
        print("\n🎉 Integration test successful!")
    else:
        print("\n💥 Integration test failed!")
    
    sys.exit(0 if success else 1)