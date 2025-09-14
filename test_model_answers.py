#!/usr/bin/env python3
"""
Test script to validate model answer extraction from parallel_sets JSON files
"""

import json
from pathlib import Path

def test_model_answer_extraction():
    """Test that model answers can be correctly extracted from parallel_sets JSON"""
    
    # Test files from the system reminder
    test_files = [
        "/Users/jihunkong/reading-json/generator/parallel_sets/set_1/paragraphs/para_20231015_7892.json",
        "/Users/jihunkong/reading-json/generator/parallel_sets/set_4/paragraphs/para_20231010_7890.json", 
        "/Users/jihunkong/reading-json/generator/parallel_sets/set_4/paragraphs/para_20231015_3872.json",
        "/Users/jihunkong/reading-json/generator/parallel_sets/set_1/paragraphs/para_20231010_7890.json"
    ]
    
    for file_path in test_files:
        if not Path(file_path).exists():
            print(f"❌ File not found: {file_path}")
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            task = json.load(f)
        
        print(f"\n📄 Testing: {task['id']}")
        print(f"   Topic: {task['topic']}")
        
        # Test multiple choice answer extraction
        print("\n   Multiple Choice Questions:")
        
        # Keywords MCQ
        q_keywords = task.get('q_keywords_mcq', {})
        keywords_answer = q_keywords.get('answer', q_keywords.get('answer_index', 'NOT_FOUND'))
        print(f"   • Keywords answer: {keywords_answer} (type: {type(keywords_answer)})")
        
        # Center sentence MCQ  
        q_center = task.get('q_center_sentence_mcq', {})
        center_answer = q_center.get('answer', q_center.get('answer_idx', q_center.get('answer_index', 'NOT_FOUND')))
        print(f"   • Center sentence answer: {center_answer} (type: {type(center_answer)})")
        
        # Free response answer extraction
        print("\n   Free Response Question:")
        q_topic = task.get('q_topic_free', {})
        topic_answer = q_topic.get('answer', q_topic.get('target_answer', q_topic.get('target_topic', 'NOT_FOUND')))
        print(f"   • Topic answer: '{topic_answer}' (type: {type(topic_answer)})")
        print(f"   • Answer length: {len(str(topic_answer)) if topic_answer != 'NOT_FOUND' else 0} characters")
        
        # Check if any answers are missing
        if keywords_answer == 'NOT_FOUND' or center_answer == 'NOT_FOUND' or topic_answer == 'NOT_FOUND':
            print("   ⚠️  Some answers not found - check field names!")
        else:
            print("   ✅ All answers found successfully")

if __name__ == "__main__":
    test_model_answer_extraction()