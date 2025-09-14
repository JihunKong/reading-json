#!/usr/bin/env python3
"""
Test the 4-Phase Learning System for Korean Summary Education

This script demonstrates and tests all phases of the learning system:
1. Component Identification
2. Necessity Judgment
3. Generalization  
4. Theme Reconstruction
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict

sys.path.append('/Users/jihunkong/reading-json')

from core.learning import (
    LearningPhaseController, EnhancedLearningTask, StudentResponse, 
    LearningPhase, ComponentType, Necessity
)

def load_enhanced_task() -> EnhancedLearningTask:
    """Load an enhanced task for testing"""
    task_file = Path("/Users/jihunkong/reading-json/data/enhanced_tasks/enhanced_para_171200_3456.json")
    
    with open(task_file, 'r', encoding='utf-8') as f:
        task_data = json.load(f)
    
    return EnhancedLearningTask.from_dict(task_data)

def simulate_student_response_phase1(correct_percentage: float = 0.8) -> Dict:
    """Simulate a student response for Phase 1"""
    
    # Simulate identifying components with some accuracy
    if correct_percentage >= 0.8:
        return {
            "sentence_id": 1,
            "identified_components": {
                "주어": ["언어는"],  # Correct
                "서술어": ["하는", "힘이다"],  # Partially correct  
                "목적어": ["도구를"],  # Correct
                "부사어": ["단순히"]  # Optional component
            }
        }
    else:
        return {
            "sentence_id": 1,
            "identified_components": {
                "주어": ["언어"],  # Missing marker
                "서술어": ["전달하는"],  # Wrong predicate
                "관형어": ["강력한"]  # Incorrect classification
            }
        }

def simulate_student_response_phase2(accuracy: float = 0.75) -> Dict:
    """Simulate student response for Phase 2"""
    
    if accuracy >= 0.75:
        return {
            "sentence_id": 1,
            "necessity_classifications": {
                "주어:언어는": "required",  # Correct
                "서술어:하는": "required",   # Correct
                "서술어:힘이다": "required", # Correct
                "목적어:도구를": "required", # Correct
                "부사어:단순히": "optional", # Correct
                "관형어:강력한": "optional"  # Correct
            }
        }
    else:
        return {
            "sentence_id": 1,
            "necessity_classifications": {
                "주어:언어는": "optional",   # WRONG - critical error
                "서술어:하는": "required",   # Correct
                "서술어:힘이다": "required", # Correct
                "부사어:단순히": "required", # WRONG
                "관형어:강력한": "decorative" # Somewhat wrong
            }
        }

def test_phase_1_component_identification():
    """Test Phase 1: Component Identification"""
    
    print("🔍 Testing Phase 1: Component Identification")
    print("=" * 60)
    
    controller = LearningPhaseController()
    task = load_enhanced_task()
    student_id = "test_student_001"
    
    # Start Phase 1
    phase1_data = controller.start_phase_1(task, student_id)
    
    print("📋 Phase 1 Setup:")
    print(f"  Objective: {phase1_data['objective']}")
    print(f"  Target sentence: {phase1_data['target_sentence']['text'][:50]}...")
    print(f"  Components to find: {phase1_data['target_sentence']['components_to_find']}")
    print(f"  Time limit: {phase1_data['interface']['time_limit']} seconds")
    
    # Test with good response
    print("\n✅ Testing with good student response (80% accuracy):")
    good_response = StudentResponse(
        student_id=student_id,
        task_id=task.id,
        phase=LearningPhase.COMPONENT_IDENTIFICATION,
        timestamp=datetime.now().isoformat(),
        response_data=simulate_student_response_phase1(0.8)
    )
    
    evaluation = controller.evaluate_phase_1(good_response, task)
    
    print(f"  Score: {evaluation.score:.2f}")
    print(f"  Correct: {evaluation.correct_components}")
    print(f"  Missing: {evaluation.missing_components}")
    print(f"  Next action: {evaluation.next_action}")
    print(f"  Mastery achieved: {evaluation.mastery_achieved}")
    
    if evaluation.hints:
        print("  Hints provided:")
        for hint in evaluation.hints:
            print(f"    Level {hint.level}: {hint.message}")
    
    # Test with poor response
    print("\n❌ Testing with poor student response (40% accuracy):")
    poor_response = StudentResponse(
        student_id=student_id,
        task_id=task.id,
        phase=LearningPhase.COMPONENT_IDENTIFICATION,
        timestamp=datetime.now().isoformat(),
        response_data=simulate_student_response_phase1(0.4)
    )
    
    evaluation = controller.evaluate_phase_1(poor_response, task)
    
    print(f"  Score: {evaluation.score:.2f}")
    print(f"  Missing: {evaluation.missing_components}")
    print(f"  Incorrect: {evaluation.incorrect_components}")
    print(f"  Next action: {evaluation.next_action}")
    
    if evaluation.hints:
        print("  Hints provided:")
        for hint in evaluation.hints:
            print(f"    Level {hint.level}: {hint.message}")

def test_phase_2_necessity_judgment():
    """Test Phase 2: Necessity Judgment"""
    
    print("\n🎯 Testing Phase 2: Necessity Judgment")
    print("=" * 60)
    
    controller = LearningPhaseController()
    task = load_enhanced_task()
    student_id = "test_student_001"
    
    # Start Phase 2
    phase2_data = controller.start_phase_2(task, student_id)
    
    print("📋 Phase 2 Setup:")
    print(f"  Objective: {phase2_data['objective']}")
    print(f"  Categories: {phase2_data['interface']['categories']}")
    print(f"  Interaction: {phase2_data['interface']['interaction_type']}")
    print(f"  Components to classify: {len(phase2_data['target_sentence']['components'])}")
    
    # Test with good response
    print("\n✅ Testing with good necessity judgment:")
    good_response = StudentResponse(
        student_id=student_id,
        task_id=task.id,
        phase=LearningPhase.NECESSITY_JUDGMENT,
        timestamp=datetime.now().isoformat(),
        response_data=simulate_student_response_phase2(0.8)
    )
    
    evaluation = controller.evaluate_phase_2(good_response, task)
    
    print(f"  Score: {evaluation.score:.2f}")
    print(f"  Correct classifications: {evaluation.correct_components}")
    print(f"  Incorrect: {len(evaluation.incorrect_components)}")
    print(f"  Next action: {evaluation.next_action}")
    print(f"  Mastery achieved: {evaluation.mastery_achieved}")
    
    # Test with poor response (critical errors)
    print("\n❌ Testing with poor necessity judgment (critical errors):")
    poor_response = StudentResponse(
        student_id=student_id,
        task_id=task.id,
        phase=LearningPhase.NECESSITY_JUDGMENT,
        timestamp=datetime.now().isoformat(),
        response_data=simulate_student_response_phase2(0.4)
    )
    
    evaluation = controller.evaluate_phase_2(poor_response, task)
    
    print(f"  Score: {evaluation.score:.2f} (with penalty for critical errors)")
    print(f"  Incorrect classifications: {len(evaluation.incorrect_components)}")
    print(f"  Next action: {evaluation.next_action}")
    
    if evaluation.hints:
        print("  Critical error hints:")
        for hint in evaluation.hints:
            print(f"    Level {hint.level}: {hint.message}")

def test_phase_3_generalization():
    """Test Phase 3: Generalization"""
    
    print("\n🔄 Testing Phase 3: Generalization")
    print("=" * 60)
    
    controller = LearningPhaseController()
    task = load_enhanced_task()
    student_id = "test_student_001"
    
    # Start Phase 3
    phase3_data = controller.start_phase_3(task, student_id)
    
    print("📋 Phase 3 Setup:")
    print(f"  Objective: {phase3_data['objective']}")
    print(f"  Interaction: {phase3_data['interface']['interaction_type']}")
    print(f"  Abstraction levels: {phase3_data['interface']['abstraction_levels']}")
    
    generalizable = phase3_data['target_sentence']['generalizable_components']
    print(f"  Generalizable components found: {len(generalizable)}")
    
    for comp in generalizable[:2]:  # Show first 2
        print(f"    '{comp['text']}' → candidates: {comp['candidates']}")

def test_phase_4_theme_reconstruction():
    """Test Phase 4: Theme Reconstruction"""
    
    print("\n🎨 Testing Phase 4: Theme Reconstruction")
    print("=" * 60)
    
    controller = LearningPhaseController()
    task = load_enhanced_task()
    student_id = "test_student_001"
    
    # Start Phase 4
    phase4_data = controller.start_phase_4(task, student_id)
    
    print("📋 Phase 4 Setup:")
    print(f"  Objective: {phase4_data['objective']}")
    print(f"  Total sentences to analyze: {len(phase4_data['all_sentences'])}")
    print(f"  Interface features: concept mapping, connection visualization")
    
    print("\n📝 Sentences to synthesize:")
    for i, sent in enumerate(phase4_data['all_sentences'], 1):
        print(f"  {i}. Role: {sent['role']} | Concept: {sent['main_concept']}")
        print(f"     Text: {sent['text'][:60]}...")
        print(f"     Importance: {sent['importance']:.2f}")

def test_student_progress_tracking():
    """Test progress tracking capabilities"""
    
    print("\n📊 Testing Student Progress Tracking")
    print("=" * 60)
    
    controller = LearningPhaseController()
    
    # Get sample progress report
    progress = controller.get_student_progress("test_student_001", "enhanced_para_171200_3456")
    
    print("📈 Student Progress Report:")
    print(f"  Current phase: {progress['current_phase']}")
    print(f"  Total attempts: {progress['attempts']}")
    print(f"  Time spent: {progress['time_spent']//60}m {progress['time_spent']%60}s")
    print(f"  Hints used: {progress['hints_used']}")
    print(f"  Overall mastery: {progress['mastery_progress']*100:.1f}%")
    
    print("\n📊 Phase Scores:")
    for phase, score in progress['phase_scores'].items():
        status = "✅" if score >= 0.8 else "🔄" if score >= 0.6 else "❌"
        print(f"  {status} {phase.replace('_', ' ').title()}: {score:.2f}")

def test_adaptive_difficulty():
    """Test adaptive difficulty system"""
    
    print("\n⚙️ Testing Adaptive Difficulty")
    print("=" * 60)
    
    controller = LearningPhaseController()
    
    # Show advancement thresholds
    print("🎯 Advancement Thresholds:")
    for phase, threshold in controller.advancement_thresholds.items():
        print(f"  {phase.value}: {threshold:.2f} ({int(threshold*100)}%)")
    
    # Test next action determination
    test_scores = [0.9, 0.75, 0.6, 0.4]
    phase = LearningPhase.COMPONENT_IDENTIFICATION
    
    print(f"\n🔍 Next Action Decision for {phase.value}:")
    for score in test_scores:
        action = controller._determine_next_action(score, phase)
        print(f"  Score {score:.1f} → {action}")

def main():
    """Run all learning phase tests"""
    
    print("🚀 Korean Summary Learning System - Phase Testing")
    print("=" * 80)
    
    try:
        # Test each phase
        test_phase_1_component_identification()
        test_phase_2_necessity_judgment()
        test_phase_3_generalization()
        test_phase_4_theme_reconstruction()
        test_student_progress_tracking()
        test_adaptive_difficulty()
        
        print("\n🎉 All learning phase tests completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()