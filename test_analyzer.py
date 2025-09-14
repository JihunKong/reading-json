#!/usr/bin/env python3
"""
Test the Korean Sentence Analyzer for summary learning system
"""

import sys
import os
sys.path.append('/Users/jihunkong/reading-json')

from core.nlp.korean_analyzer import KoreanSentenceAnalyzer, SentenceAnalysis

def test_comprehensive_analysis():
    """Test comprehensive sentence analysis functionality"""
    
    print("=== Korean Sentence Analyzer Test ===\n")
    
    # Initialize analyzer
    analyzer = KoreanSentenceAnalyzer()
    
    # Test sentences with different complexity levels
    test_sentences = [
        "민주주의는 자유와 평등을 바탕으로 사회적 영향력을 행사하는 강력한 힘이다.",
        "책을 읽는다.",
        "학생들이 도서관에서 열심히 공부하고 있다.",
        "현대 사회에서 과학 기술의 발전은 인간의 삶을 크게 변화시켰다."
    ]
    
    for i, sentence in enumerate(test_sentences, 1):
        print(f"📝 Test Sentence {i}: {sentence}")
        print("-" * 60)
        
        try:
            # Analyze sentence
            analysis = analyzer.analyze_sentence(sentence)
            
            # Display results
            print(f"🎯 Main Concept: {analysis.main_concept}")
            print(f"📊 Sentence Role: {analysis.sentence_role}")
            print(f"⭐ Importance Score: {analysis.importance_score:.2f}")
            print(f"🔍 Complexity: {analysis.complexity_level}")
            
            print("\n📋 Grammatical Components:")
            for comp_type, components in analysis.components.items():
                if components:
                    print(f"  {comp_type}:")
                    for comp in components:
                        necessity_emoji = "🔴" if comp.necessity == "required" else "🟡" if comp.necessity == "optional" else "⚪"
                        print(f"    {necessity_emoji} {comp.text} (importance: {comp.importance_score:.2f})")
            
            # Test summary component extraction
            summary_components = analyzer.extract_summary_components(analysis)
            print(f"\n📝 Summary Components:")
            print(f"  Essential: {summary_components['essential']}")
            print(f"  Optional: {summary_components['optional']}")
            print(f"  Removable: {summary_components['removable']}")
            
            # Test learning hints with a sample user attempt
            user_summary = sentence[:10] + "..."  # Simplified mock summary
            hints = analyzer.generate_learning_hints(analysis, user_summary)
            if hints:
                print(f"\n💡 Learning Hints:")
                for hint in hints:
                    print(f"  • {hint}")
            
        except Exception as e:
            print(f"❌ Error analyzing sentence: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "="*80 + "\n")
    
    # Test paragraph analysis
    print("📄 Paragraph Analysis Test:")
    paragraph = """
    민주주의는 자유와 평등을 바탕으로 하는 정치 체제이다. 
    시민들의 적극적인 참여가 민주주의의 핵심 요소이다.
    따라서 민주주의 사회에서는 개인의 권리와 책임이 균형을 이루어야 한다.
    """.strip()
    
    try:
        paragraph_analyses = analyzer.analyze_paragraph(paragraph)
        
        print(f"📊 Total sentences: {len(paragraph_analyses)}")
        for i, analysis in enumerate(paragraph_analyses, 1):
            print(f"  Sentence {i}: {analysis.sentence_role} (importance: {analysis.importance_score:.2f})")
            print(f"    Main concept: {analysis.main_concept}")
            print(f"    Text: {analysis.original_text}")
        
    except Exception as e:
        print(f"❌ Error in paragraph analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_comprehensive_analysis()