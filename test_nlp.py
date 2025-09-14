#!/usr/bin/env python3
"""
Test script for Korean NLP functionality using KoNLPy
"""

from konlpy.tag import Mecab, Okt
import sys

def test_korean_nlp():
    """Test Korean NLP analyzers"""
    
    # Test sentence - complex Korean text with various components
    test_sentence = "민주주의는 자유와 평등을 바탕으로 사회적 영향력을 행사하는 강력한 힘이다."
    
    print("=== Korean NLP Test ===")
    print(f"Test sentence: {test_sentence}")
    print()
    
    # Try Mecab first (most accurate)
    try:
        mecab = Mecab()
        print("✅ Mecab analyzer available")
        
        # Morphological analysis
        morphs = mecab.morphs(test_sentence)
        print(f"Morphemes: {morphs}")
        
        # POS tagging
        pos_tags = mecab.pos(test_sentence)
        print(f"POS tags: {pos_tags}")
        
        # Extract sentence components
        components = extract_sentence_components(pos_tags)
        print(f"Sentence components: {components}")
        
    except Exception as e:
        print(f"❌ Mecab not available: {e}")
        print("Trying Okt (Open Korean Text) analyzer...")
        
        # Fallback to Okt
        try:
            okt = Okt()
            print("✅ Okt analyzer available")
            
            morphs = okt.morphs(test_sentence)
            print(f"Morphemes: {morphs}")
            
            pos_tags = okt.pos(test_sentence)
            print(f"POS tags: {pos_tags}")
            
            components = extract_sentence_components(pos_tags)
            print(f"Sentence components: {components}")
            
        except Exception as e:
            print(f"❌ Okt also failed: {e}")
            return False
    
    return True

def extract_sentence_components(pos_tags):
    """Extract basic sentence components from POS tags"""
    components = {
        'subjects': [],      # 주어 
        'predicates': [],    # 서술어
        'objects': [],       # 목적어
        'modifiers': [],     # 관형어
        'adverbs': []        # 부사어
    }
    
    for word, pos in pos_tags:
        # Subject markers (은/는, 이/가)
        if pos in ['JX', 'JKS']:  # 보조사, 주격조사
            if word in ['는', '은', '이', '가']:
                components['subjects'].append((word, pos))
        
        # Predicates (verbs and adjectives)
        elif pos.startswith('V'):  # 동사
            components['predicates'].append((word, pos))
        elif pos.startswith('XSV'):  # 동사 파생 접미사
            components['predicates'].append((word, pos))
            
        # Objects (을/를 markers)
        elif pos == 'JKO':  # 목적격조사
            components['objects'].append((word, pos))
            
        # Modifiers (관형어)
        elif pos in ['MM', 'MAG']:  # 관형사, 일반부사
            components['modifiers'].append((word, pos))
            
        # Adverbials
        elif pos.startswith('MAG'):  # 부사
            components['adverbs'].append((word, pos))
    
    return components

if __name__ == "__main__":
    success = test_korean_nlp()
    if success:
        print("\n✅ Korean NLP setup successful!")
    else:
        print("\n❌ Korean NLP setup failed!")
        sys.exit(1)