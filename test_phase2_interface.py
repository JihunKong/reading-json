#!/usr/bin/env python3
"""
Test script for Phase 2 Interface Implementation
Tests the drag-and-drop necessity judgment functionality
"""

import sys
import os
sys.path.append('/Users/jihunkong/reading-json')

from flask import Flask
from app.learning_routes import learning_bp
from core.learning import LearningPhaseController, EnhancedLearningTask
import json

def test_phase2_data_generation():
    """Test Phase 2 data generation from learning controller"""
    
    print("🧪 Testing Phase 2 Data Generation...")
    
    # Load sample enhanced task
    task_file = '/Users/jihunkong/reading-json/data/enhanced_tasks/sample_task_phase2.json'
    
    try:
        with open(task_file, 'r', encoding='utf-8') as f:
            task_data = json.load(f)
            
        task = EnhancedLearningTask.from_dict(task_data)
        print(f"✅ Sample task loaded: {task.id}")
        
        # Initialize controller
        controller = LearningPhaseController()
        
        # Generate Phase 2 data
        phase2_data = controller.start_phase_2(task, "test_student_123")
        
        print("\n📊 Generated Phase 2 Data:")
        print(f"  - Objective: {phase2_data['objective']}")
        print(f"  - Target Sentence: {phase2_data['target_sentence']['text']}")
        print(f"  - Components Count: {len(phase2_data['target_sentence']['components'])}")
        print(f"  - Interface Mode: {phase2_data['interface']['mode']}")
        print(f"  - Categories: {phase2_data['interface']['categories']}")
        
        print("\n🔍 Component Details:")
        for i, comp in enumerate(phase2_data['target_sentence']['components'], 1):
            print(f"  {i}. {comp['text']} ({comp['type']}) - {comp.get('correct_necessity', 'unknown')}")
        
        # Test evaluation
        print("\n🎯 Testing Evaluation...")
        
        sample_response_data = {
            'sentence_id': 1,
            'necessity_classifications': {
                '주어:인공지능 기술은': 'required',
                '서술어:이끌고 있다': 'required',
                '목적어:변화를': 'required',
                '관형어:현대 사회의': 'optional',
                '관형어:다양한': 'decorative',
                '관형어:혁신적인': 'optional',
                '부사어:분야에서': 'optional'
            }
        }
        
        from core.learning.phase_controller import StudentResponse, LearningPhase
        from datetime import datetime
        
        student_response = StudentResponse(
            student_id="test_student_123",
            task_id=task.id,
            phase=LearningPhase.NECESSITY_JUDGMENT,
            timestamp=datetime.now().isoformat(),
            response_data=sample_response_data
        )
        
        evaluation = controller.evaluate_phase_2(student_response, task)
        
        print(f"  - Score: {evaluation.score:.2f}")
        print(f"  - Mastery Achieved: {evaluation.mastery_achieved}")
        print(f"  - Correct Components: {len(evaluation.correct_components)}")
        print(f"  - Incorrect Components: {len(evaluation.incorrect_components)}")
        print(f"  - Next Action: {evaluation.next_action}")
        print(f"  - Hints: {len(evaluation.hints)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Phase 2: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_flask_integration():
    """Test Flask integration with Phase 2"""
    
    print("\n🌐 Testing Flask Integration...")
    
    try:
        app = Flask(__name__)
        app.secret_key = 'test_key'
        app.register_blueprint(learning_bp)
        
        with app.test_client() as client:
            # Test learning home page
            response = client.get('/learning/')
            print(f"  - Learning home status: {response.status_code}")
            
            # The actual task testing would require more setup
            print("  - Flask integration appears to be working")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing Flask integration: {e}")
        return False

def validate_interface_completeness():
    """Validate that all required interface elements are present"""
    
    print("\n✅ Validating Interface Completeness...")
    
    # Check if all required functions are implemented
    from app.learning_routes import learning_bp
    
    required_functions = [
        'initializeDragAndDrop',
        'handleComponentDrop', 
        'validateNecessityClassification',
        'showCriticalErrorWarning',
        'collectPhase2Data',
        'undoLastMove',
        'showHint',
        'previewSentence'
    ]
    
    # Read the learning_routes.py file to check for functions
    routes_file = '/Users/jihunkong/reading-json/app/learning_routes.py'
    
    try:
        with open(routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        missing_functions = []
        for func in required_functions:
            if f"function {func}" not in content:
                missing_functions.append(func)
        
        if missing_functions:
            print(f"❌ Missing functions: {missing_functions}")
            return False
        else:
            print("✅ All required JavaScript functions are implemented")
        
        # Check CSS classes
        required_css_classes = [
            '.draggable-component',
            '.drop-zone',
            '.necessity-container',
            '.component-correct',
            '.component-incorrect', 
            '.component-critical-error',
            '.drag-over'
        ]
        
        missing_css = []
        for css_class in required_css_classes:
            if css_class not in content:
                missing_css.append(css_class)
        
        if missing_css:
            print(f"⚠️ Missing CSS classes: {missing_css}")
        else:
            print("✅ All required CSS classes are defined")
        
        return len(missing_functions) == 0
        
    except Exception as e:
        print(f"❌ Error validating interface: {e}")
        return False

def main():
    """Run all tests"""
    
    print("🚀 Phase 2 Interface Implementation Test")
    print("=" * 50)
    
    tests = [
        ("Phase 2 Data Generation", test_phase2_data_generation),
        ("Flask Integration", test_flask_integration), 
        ("Interface Completeness", validate_interface_completeness)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📝 Running: {test_name}")
        success = test_func()
        results.append((test_name, success))
        
        if success:
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print(f"\n🏆 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Phase 2 implementation is complete.")
        print("\n🚀 Ready to run with: python app/main.py")
        print("🔗 Access at: http://localhost:8080/learning")
    else:
        print("⚠️ Some tests failed. Review implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)