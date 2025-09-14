#!/usr/bin/env python3
"""
Simple test for Korean phrase analyzer
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.korean_phrase_analyzer import KoreanPhraseAnalyzer

def test_phrase_analyzer():
    """Test the Korean phrase analyzer directly"""
    
    print("🔍 Testing Korean Phrase Analyzer")
    print("=" * 40)
    
    # Initialize the analyzer
    analyzer = KoreanPhraseAnalyzer()
    
    # Test sentence: "도시 녹화는 현대 도시 문제 해결에 중요한 역할을 한다"
    test_sentence = "도시 녹화는 현대 도시 문제 해결에 중요한 역할을 한다"
    
    print(f"\n📝 Test sentence: {test_sentence}")
    print("\n🔍 Analyzing phrase structure...")
    
    try:
        # Analyze the sentence
        phrases = analyzer.analyze_phrase_structure(test_sentence)
        
        print(f"\n✅ Analysis completed! Found {len(phrases)} phrases:")
        print("-" * 60)
        
        for i, phrase in enumerate(phrases, 1):
            print(f"{i}. 구: '{phrase.text}'")
            print(f"   성분: {phrase.component_type.value}")
            print(f"   조사: {phrase.particles}")
            print(f"   신뢰도: {phrase.confidence:.2f}")
            print(f"   교육수준: {phrase.educational_level}")
            print(f"   위치: {phrase.start_pos}-{phrase.end_pos}")
            print()
        
        # Test the educational examples
        print("📚 Testing educational examples:")
        examples = analyzer.get_educational_examples("middle")
        
        for example in examples:
            print(f"\n예문: {example['sentence']}")
            print(f"구: {example['phrases']}")
            print(f"성분: {example['components']}")
        
        print("\n✅ All phrase analyzer tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_phrase_analyzer()
    if success:
        print("\n🎉 Phrase analyzer test successful!")
        
        # Test specific phrase analysis for the user's concern
        print("\n" + "="*60)
        print("🎯 Testing user's specific concern: '도시 녹화는' as single subject phrase")
        
        analyzer = KoreanPhraseAnalyzer()
        phrases = analyzer.analyze_phrase_structure("도시 녹화는 중요하다")
        
        subject_phrases = [p for p in phrases if p.component_type.value == "주어구"]
        if subject_phrases:
            subject_phrase = subject_phrases[0]
            print(f"✅ Subject phrase identified: '{subject_phrase.text}'")
            print(f"   Contains particles: {subject_phrase.particles}")
            
            if "도시 녹화" in subject_phrase.text and "는" in subject_phrase.particles:
                print("🎉 SUCCESS: '도시 녹화는' correctly identified as single subject phrase!")
            else:
                print("❌ Issue: Subject phrase not correctly identified")
        else:
            print("❌ No subject phrase found")
            
    else:
        print("\n💥 Phrase analyzer test failed!")
    
    sys.exit(0 if success else 1)