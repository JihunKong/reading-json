"""
Korean Phrase-Level Grammar Analyzer
한국어 구 단위 문법 분석기

This module provides phrase-level analysis for Korean sentences,
properly handling Korean grammatical structures including particles,
relative clauses, and complex sentence components.
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import re
from konlpy.tag import Okt

class ComponentType(Enum):
    """Korean sentence component types (구 단위)"""
    SUBJECT = "주어구"          # Subject phrase: 도시 녹화는
    PREDICATE = "서술어구"      # Predicate phrase: 중요한 역할을 한다
    OBJECT = "목적어구"         # Object phrase: 현대 도시 문제 해결을
    COMPLEMENT = "보어구"       # Complement phrase: 학생이 되었다
    ADVERBIAL = "부사어구"      # Adverbial phrase: 매우 빠르게
    MODIFIER = "관형어구"       # Modifier phrase: 아름다운 봄날의

@dataclass
class PhraseUnit:
    """Korean grammatical phrase unit"""
    text: str                    # Full phrase text
    start_pos: int              # Starting character position
    end_pos: int                # Ending character position
    component_type: ComponentType # Grammatical function
    tokens: List[Dict]          # Individual tokens with POS tags
    particles: List[str]        # Associated particles (조사)
    confidence: float           # Analysis confidence (0.0-1.0)
    educational_level: str      # elementary/middle/high
    
    def __str__(self):
        return f"{self.text} ({self.component_type.value})"

@dataclass
class KoreanParticle:
    """Korean particle (조사) information"""
    text: str                   # Particle text (은, 는, 이, 가, etc.)
    type: str                   # subject, object, topic, etc.
    attached_word: str          # Word it's attached to
    position: int               # Position in sentence

class KoreanPhraseAnalyzer:
    """
    Advanced Korean phrase-level grammar analyzer
    한국어 구 단위 문법 분석기
    """
    
    def __init__(self):
        self.okt = Okt()
        
        # Korean particles by function (조사 체계)
        self.particles = {
            'subject': ['이', '가'],           # 주격조사
            'topic': ['은', '는'],             # 주제조사
            'object': ['을', '를'],            # 목적격조사
            'complement': ['이', '가'],        # 보격조사
            'adverbial': ['에', '에서', '로', '으로', '와', '과', '하고'],  # 부사격조사
            'possessive': ['의'],              # 관형격조사
        }
        
        # Phrase boundary indicators
        self.phrase_boundaries = {
            'clause_endings': ['은', '는', '이', '가', '을', '를', '에게', '한테', '에서', '로'],
            'verb_endings': ['다', '요', '니다', '습니다', '어요', '아요'],
            'modifier_endings': ['은', '는', '던', '을', '를'],
        }
        
        # Complex structure patterns
        self.complex_patterns = {
            'relative_clause': r'(\w+이?\w*)\s+(\w+은|는)\s+(\w+)',  # 학생이 읽은 책은
            'noun_clause': r'(\w+기가?)\s+(\w+다)',                 # 공부하기가 어렵다
            'embedded': r'(\[.*?\])',                              # [그가 말한] 내용
        }
        
        print("✅ Korean Phrase Analyzer initialized")
    
    def analyze_phrase_structure(self, sentence: str) -> List[PhraseUnit]:
        """
        Analyze Korean sentence into grammatically correct phrase units
        문장을 문법적으로 올바른 구 단위로 분석
        """
        print(f"🔍 구 단위 분석 시작: {sentence}")
        
        # Step 1: Tokenize with POS tags
        tokens = self.okt.pos(sentence, norm=True, stem=False)
        print(f"📝 형태소 분석: {tokens}")
        
        # Step 2: Identify particles and boundaries
        particles = self._identify_particles(tokens)
        print(f"🏷️ 조사 식별: {particles}")
        
        # Step 3: Determine phrase boundaries
        phrases = self._determine_phrase_boundaries(sentence, tokens, particles)
        print(f"🎯 구 경계 설정: {[p.text for p in phrases]}")
        
        # Step 4: Classify phrase components
        classified_phrases = self._classify_phrase_components(phrases)
        print(f"✅ 성분 분류 완료: {[(p.text, p.component_type.value) for p in classified_phrases]}")
        
        return classified_phrases
    
    def _identify_particles(self, tokens: List[Tuple[str, str]]) -> List[KoreanParticle]:
        """Identify Korean particles in the token sequence"""
        particles = []
        
        for i, (word, pos) in enumerate(tokens):
            if pos in ['Josa']:  # Korean particle POS tag
                # Find the word this particle is attached to
                attached_word = tokens[i-1][0] if i > 0 else ""
                
                # Determine particle function
                particle_type = self._classify_particle_function(word)
                
                particles.append(KoreanParticle(
                    text=word,
                    type=particle_type,
                    attached_word=attached_word,
                    position=i
                ))
        
        return particles
    
    def _classify_particle_function(self, particle: str) -> str:
        """Classify the grammatical function of a Korean particle"""
        for function, particle_list in self.particles.items():
            if particle in particle_list:
                return function
        return 'unknown'
    
    def _determine_phrase_boundaries(self, sentence: str, tokens: List[Tuple[str, str]], 
                                   particles: List[KoreanParticle]) -> List[PhraseUnit]:
        """
        Determine phrase boundaries based on Korean grammar rules
        한국어 문법 규칙에 따른 구 경계 설정
        """
        phrases = []
        current_phrase_start = 0
        current_tokens = []
        
        for i, (word, pos) in enumerate(tokens):
            current_tokens.append({'word': word, 'pos': pos, 'index': i})
            
            # Check if this is a phrase boundary
            is_boundary = self._is_phrase_boundary(word, pos, i, tokens, particles)
            
            if is_boundary or i == len(tokens) - 1:  # End of phrase or sentence
                # Create phrase unit
                phrase_text = self._reconstruct_phrase_text(current_tokens)
                phrase_particles = [p for p in particles if current_phrase_start <= p.position <= i]
                
                phrase = PhraseUnit(
                    text=phrase_text.strip(),
                    start_pos=current_phrase_start,
                    end_pos=i,
                    component_type=ComponentType.SUBJECT,  # Will be classified later
                    tokens=current_tokens,
                    particles=[p.text for p in phrase_particles],
                    confidence=0.8,
                    educational_level="middle"
                )
                
                if phrase.text:  # Only add non-empty phrases
                    phrases.append(phrase)
                
                # Reset for next phrase
                current_phrase_start = i + 1
                current_tokens = []
        
        # Post-process: combine single particle phrases with previous phrases
        phrases = self._merge_single_particles(phrases)
        
        return phrases
    
    def _merge_single_particles(self, phrases: List[PhraseUnit]) -> List[PhraseUnit]:
        """Merge single particle phrases with appropriate adjacent phrases"""
        if len(phrases) <= 1:
            return phrases
        
        merged_phrases = []
        i = 0
        
        while i < len(phrases):
            current_phrase = phrases[i]
            
            # Check if this is a single particle phrase that should be merged
            if (len(current_phrase.tokens) == 1 and 
                current_phrase.tokens[0]['pos'] == 'Josa' and
                i > 0):  # Has a previous phrase to merge with
                
                # Merge with previous phrase
                prev_phrase = merged_phrases[-1]
                
                # Combine tokens, particles, and text
                combined_tokens = prev_phrase.tokens + current_phrase.tokens
                combined_particles = prev_phrase.particles + current_phrase.particles
                combined_text = prev_phrase.text + ' ' + current_phrase.text
                
                # Create merged phrase
                merged_phrase = PhraseUnit(
                    text=combined_text.strip(),
                    start_pos=prev_phrase.start_pos,
                    end_pos=current_phrase.end_pos,
                    component_type=prev_phrase.component_type,
                    tokens=combined_tokens,
                    particles=combined_particles,
                    confidence=min(prev_phrase.confidence, current_phrase.confidence),
                    educational_level=prev_phrase.educational_level
                )
                
                # Replace the previous phrase with merged phrase
                merged_phrases[-1] = merged_phrase
                
            else:
                # Regular phrase, add as-is
                merged_phrases.append(current_phrase)
            
            i += 1
        
        return merged_phrases
    
    def _is_phrase_boundary(self, word: str, pos: str, index: int, 
                          tokens: List[Tuple[str, str]], particles: List[KoreanParticle]) -> bool:
        """Determine if current position is a phrase boundary"""
        
        # Core Korean particle boundaries - these ALWAYS end phrases
        if pos == 'Josa':
            # Major phrase-ending particles
            phrase_ending_particles = {
                # Subject/topic markers
                '은', '는', '이', '가',
                # Object markers  
                '을', '를',
                # Adverbial/locative markers
                '에', '에서', '로', '으로',
                # Complement markers
                '와', '과', '하고', '이나', '나',
                # Possessive marker when it ends a modifier phrase
                '의'
            }
            
            if word in phrase_ending_particles:
                return True
        
        # Length-based boundary: prevent overly long phrases (max 5 content words)
        if index > 0:
            # Count content words from start of current phrase
            content_word_count = 0
            phrase_start = self._find_current_phrase_start(index, tokens)
            
            for i in range(phrase_start, index + 1):
                token_pos = tokens[i][1]
                if token_pos in ['Noun', 'Verb', 'Adjective', 'Adverb']:
                    content_word_count += 1
                    
            # Force boundary if phrase getting too long
            if content_word_count >= 4:  # Max 4 content words per phrase
                return True
        
        # Verb-based boundaries (end of predicate phrases)
        if pos in ['Verb', 'Adjective'] and index < len(tokens) - 1:
            next_word, next_pos = tokens[index + 1]
            if next_pos != 'Eomi':  # Not a verb ending
                return False
        
        # Complex structure boundaries
        if self._is_complex_structure_boundary(word, pos, index, tokens):
            return True
        
        return False
    
    def _find_current_phrase_start(self, current_index: int, tokens: List[Tuple[str, str]]) -> int:
        """Find the start of the current phrase by looking backwards for the last boundary"""
        for i in range(current_index - 1, -1, -1):
            word, pos = tokens[i]
            if pos == 'Josa':
                # Found a particle, so phrase starts after this
                return i + 1
        # If no particle found, phrase starts at beginning
        return 0
    
    def _is_complex_structure_boundary(self, word: str, pos: str, index: int, 
                                     tokens: List[Tuple[str, str]]) -> bool:
        """Handle complex Korean structures like relative clauses"""
        
        # Relative clause patterns: ~은/는/던 + noun
        if pos == 'Eomi' and word in ['은', '는', '던']:
            if index + 1 < len(tokens) and tokens[index + 1][1] == 'Noun':
                return True
        
        # Noun clause patterns: ~기가/는
        if word.endswith('기') and index + 1 < len(tokens):
            next_word = tokens[index + 1][0]
            if next_word in ['가', '는', '을', '를']:
                return True
        
        return False
    
    def _reconstruct_phrase_text(self, tokens: List[Dict]) -> str:
        """Reconstruct phrase text from tokens"""
        return ' '.join([token['word'] for token in tokens])
    
    def _classify_phrase_components(self, phrases: List[PhraseUnit]) -> List[PhraseUnit]:
        """
        Classify phrases into Korean grammatical components
        구를 한국어 문법 성분으로 분류
        """
        for phrase in phrases:
            # Classify based on particles and structure
            component_type = self._determine_component_type(phrase)
            phrase.component_type = component_type
            
            # Set educational level based on complexity
            phrase.educational_level = self._determine_educational_level(phrase)
            
            # Calculate confidence based on clear grammatical indicators
            phrase.confidence = self._calculate_confidence(phrase)
        
        return phrases
    
    def _determine_component_type(self, phrase: PhraseUnit) -> ComponentType:
        """Determine the grammatical component type of a phrase"""
        
        # Check particles first (most reliable indicator)
        for particle in phrase.particles:
            if particle in ['은', '는']:
                return ComponentType.SUBJECT  # Topic/Subject
            elif particle in ['이', '가']:
                return ComponentType.SUBJECT  # Subject
            elif particle in ['을', '를']:
                return ComponentType.OBJECT   # Object
            elif particle in ['에', '에서', '로']:
                return ComponentType.ADVERBIAL  # Adverbial
        
        # Check token patterns for predicates
        verb_count = sum(1 for token in phrase.tokens if token['pos'] in ['Verb', 'Adjective'])
        if verb_count > 0:
            return ComponentType.PREDICATE
        
        # Default classification based on position and structure
        return ComponentType.SUBJECT
    
    def _determine_educational_level(self, phrase: PhraseUnit) -> str:
        """Determine appropriate educational level for this phrase"""
        
        # Simple phrases: elementary
        if len(phrase.tokens) <= 2 and not any(t['pos'] in ['Eomi', 'Etm'] for t in phrase.tokens):
            return "elementary"
        
        # Complex phrases: high school
        if len(phrase.tokens) > 4 or any(t['word'].endswith(('기', '음', '던')) for t in phrase.tokens):
            return "high"
        
        # Default: middle school
        return "middle"
    
    def _calculate_confidence(self, phrase: PhraseUnit) -> float:
        """Calculate analysis confidence based on grammatical clarity"""
        confidence = 0.5  # Base confidence
        
        # Higher confidence for clear particle indicators
        if phrase.particles:
            confidence += 0.3
        
        # Higher confidence for clear verb patterns
        if any(t['pos'] in ['Verb', 'Adjective'] for t in phrase.tokens):
            confidence += 0.2
        
        # Lower confidence for very short or very long phrases
        if len(phrase.tokens) < 1 or len(phrase.tokens) > 6:
            confidence -= 0.1
        
        return min(1.0, max(0.0, confidence))
    
    def get_educational_examples(self, level: str = "middle") -> List[Dict]:
        """
        Get educational examples for Korean phrase analysis
        교육용 구 분석 예제 제공
        """
        examples = {
            "elementary": [
                {
                    "sentence": "학생이 공부한다",
                    "phrases": ["학생이", "공부한다"],
                    "components": ["주어구", "서술어구"]
                },
                {
                    "sentence": "고양이가 물을 마신다",
                    "phrases": ["고양이가", "물을", "마신다"],
                    "components": ["주어구", "목적어구", "서술어구"]
                }
            ],
            "middle": [
                {
                    "sentence": "도시 녹화는 현대 도시 문제 해결에 중요한 역할을 한다",
                    "phrases": ["도시 녹화는", "현대 도시 문제 해결에", "중요한 역할을", "한다"],
                    "components": ["주어구", "부사어구", "목적어구", "서술어구"]
                }
            ],
            "high": [
                {
                    "sentence": "학생이 읽은 책은 매우 흥미로웠다",
                    "phrases": ["학생이 읽은 책은", "매우 흥미로웠다"],
                    "components": ["주어구(관형절포함)", "서술어구"]
                }
            ]
        }
        
        return examples.get(level, examples["middle"])

# Test the analyzer
if __name__ == "__main__":
    analyzer = KoreanPhraseAnalyzer()
    test_sentence = "도시 녹화는 현대 도시 문제 해결에 중요한 역할을 한다"
    phrases = analyzer.analyze_phrase_structure(test_sentence)
    
    print("\n=== 분석 결과 ===")
    for phrase in phrases:
        print(f"구: {phrase.text}")
        print(f"성분: {phrase.component_type.value}")
        print(f"조사: {phrase.particles}")
        print(f"신뢰도: {phrase.confidence:.2f}")
        print("---")