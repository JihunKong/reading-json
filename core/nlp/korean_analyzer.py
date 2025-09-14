#!/usr/bin/env python3
"""
Korean Sentence Analyzer for Summary Learning System

This module provides comprehensive Korean language analysis for educational purposes,
specifically designed to support summary writing skill development.
"""

from typing import Dict, List, Tuple, Optional, Union
import re
from dataclasses import dataclass
from konlpy.tag import Okt, Mecab
import json
import os
from functools import lru_cache

@dataclass
class SentenceComponent:
    """Represents a grammatical component in a Korean sentence"""
    text: str
    pos_tag: str
    component_type: str  # 주어, 서술어, 목적어, 보어, 부사어, 관형어
    necessity: str  # required, optional, decorative
    importance_score: float  # 0-1 scale
    start_pos: int
    end_pos: int
    modifiers: List['SentenceComponent'] = None

@dataclass
class SentenceAnalysis:
    """Complete analysis of a Korean sentence"""
    original_text: str
    components: Dict[str, List[SentenceComponent]]
    sentence_role: str  # topic, supporting, example, conclusion, transition
    importance_score: float
    complexity_level: str  # simple, compound, complex
    main_concept: str
    
class KoreanSentenceAnalyzer:
    """
    Comprehensive Korean sentence analyzer for educational applications.
    
    Analyzes Korean sentences to identify:
    - Grammatical components (주어, 서술어, 목적어, 보어, 부사어, 관형어)
    - Component necessity levels
    - Sentence roles and importance
    - Learning difficulty classification
    """
    
    def __init__(self, use_mecab: bool = False, cache_size: int = 1000):
        """
        Initialize the Korean analyzer.
        
        Args:
            use_mecab: Whether to use Mecab (more accurate) or Okt (more stable)
            cache_size: Size of analysis cache for performance
        """
        self.cache_size = cache_size
        
        # Initialize NLP analyzer
        try:
            if use_mecab:
                self.analyzer = Mecab()
                self.analyzer_type = "mecab"
            else:
                raise ImportError("Using Okt as default")
        except ImportError:
            self.analyzer = Okt()
            self.analyzer_type = "okt"
            
        print(f"✅ Korean analyzer initialized: {self.analyzer_type}")
        
        # Load grammatical patterns and rules
        self._load_grammar_patterns()
        
    def _load_grammar_patterns(self):
        """Load Korean grammatical patterns for component identification"""
        
        # Subject markers (주어 표지)
        self.subject_markers = {
            'okt': ['는', '은', '이', '가'],
            'mecab': ['는', '은', '이', '가', 'JX', 'JKS']
        }
        
        # Object markers (목적어 표지) 
        self.object_markers = {
            'okt': ['을', '를'],
            'mecab': ['을', '를', 'JKO']
        }
        
        # Complement markers (보어 표지)
        self.complement_markers = {
            'okt': ['으로', '로', '에', '에게', '에서'],
            'mecab': ['으로', '로', '에', '에게', '에서', 'JKB']
        }
        
        # Adverbial markers (부사어 표지)
        self.adverbial_markers = {
            'okt': ['게', '히', '이', '으로', '로'],
            'mecab': ['게', '히', '이', '으로', '로', 'MAG']
        }
        
        # Predicate POS tags (서술어)
        self.predicate_pos = {
            'okt': ['Verb', 'Adjective'],
            'mecab': ['VV', 'VA', 'VX', 'VCP', 'VCN']
        }
        
        # Modifier POS tags (관형어)
        self.modifier_pos = {
            'okt': ['Determiner'],
            'mecab': ['MM', 'VV+ETM', 'VA+ETM']
        }
        
        # Sentence ending patterns
        self.sentence_endings = [
            'ㄴ다', '는다', '다', '이다', '했다', '한다', '될', '된', '될 것이다'
        ]
        
    @lru_cache(maxsize=1000)
    def analyze_sentence(self, sentence: str) -> SentenceAnalysis:
        """
        Perform comprehensive analysis of a Korean sentence.
        
        Args:
            sentence: Korean sentence to analyze
            
        Returns:
            SentenceAnalysis object with complete grammatical breakdown
        """
        # Clean and normalize sentence
        cleaned_sentence = self._normalize_sentence(sentence)
        
        # Get POS tags
        pos_tags = self.analyzer.pos(cleaned_sentence)
        
        # Extract grammatical components
        components = self._extract_components(pos_tags, cleaned_sentence)
        
        # Determine sentence role and importance
        sentence_role = self._classify_sentence_role(components, cleaned_sentence)
        importance_score = self._calculate_importance_score(components, sentence_role)
        
        # Assess complexity
        complexity_level = self._assess_complexity(components, pos_tags)
        
        # Extract main concept
        main_concept = self._extract_main_concept(components)
        
        return SentenceAnalysis(
            original_text=sentence,
            components=components,
            sentence_role=sentence_role,
            importance_score=importance_score,
            complexity_level=complexity_level,
            main_concept=main_concept
        )
    
    def _normalize_sentence(self, sentence: str) -> str:
        """Normalize Korean sentence for analysis"""
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', sentence.strip())
        
        # Ensure proper punctuation spacing
        normalized = re.sub(r'([.!?])', r'\1 ', normalized).strip()
        
        return normalized
    
    def _extract_components(self, pos_tags: List[Tuple[str, str]], sentence: str) -> Dict[str, List[SentenceComponent]]:
        """Extract grammatical components from POS tags"""
        
        components = {
            '주어': [],      # Subject
            '서술어': [],    # Predicate  
            '목적어': [],    # Object
            '보어': [],      # Complement
            '부사어': [],    # Adverbial
            '관형어': []     # Modifier
        }
        
        current_pos = 0
        
        for i, (word, pos) in enumerate(pos_tags):
            start_pos = current_pos
            end_pos = current_pos + len(word)
            
            # Determine component type and necessity
            component_type, necessity, importance = self._classify_component(
                word, pos, pos_tags, i
            )
            
            if component_type:
                component = SentenceComponent(
                    text=word,
                    pos_tag=pos,
                    component_type=component_type,
                    necessity=necessity,
                    importance_score=importance,
                    start_pos=start_pos,
                    end_pos=end_pos
                )
                
                components[component_type].append(component)
            
            current_pos = end_pos + 1  # Account for spaces
        
        # Post-process to identify complex components
        components = self._identify_complex_components(components, pos_tags)
        
        return components
    
    def _classify_component(self, word: str, pos: str, pos_tags: List[Tuple[str, str]], 
                          index: int) -> Tuple[Optional[str], str, float]:
        """
        Classify a word as a specific grammatical component.
        
        Returns:
            (component_type, necessity, importance_score)
        """
        
        # Get context (previous and next words)
        prev_word = pos_tags[index-1][0] if index > 0 else ""
        next_word = pos_tags[index+1][0] if index < len(pos_tags)-1 else ""
        
        markers = self.subject_markers.get(self.analyzer_type, [])
        
        # Subject identification (주어)
        if (word in markers and word in ['는', '은', '이', '가']) or pos == 'JKS':
            # The noun before this marker is the subject
            if index > 0:
                return '주어', 'required', 0.9
        
        # Predicate identification (서술어)
        if pos in self.predicate_pos.get(self.analyzer_type, []):
            necessity = 'required'
            importance = 0.95 if self._is_main_verb(word, pos_tags, index) else 0.7
            return '서술어', necessity, importance
        
        # Object identification (목적어)
        if (word in self.object_markers.get(self.analyzer_type, []) and 
            word in ['을', '를']) or pos == 'JKO':
            if index > 0:
                return '목적어', 'required', 0.8
        
        # Complement identification (보어)
        if word in self.complement_markers.get(self.analyzer_type, []):
            return '보어', 'optional', 0.6
        
        # Adverbial identification (부사어)
        if (pos in ['Adverb'] or 
            word.endswith('게') or word.endswith('히') or
            word.endswith('이')):
            necessity = 'optional' if self._is_descriptive_adverb(word) else 'required'
            importance = 0.5 if necessity == 'optional' else 0.7
            return '부사어', necessity, importance
        
        # Modifier identification (관형어)
        if (pos in ['Adjective'] and index < len(pos_tags) - 1 and
            pos_tags[index + 1][1] in ['Noun']):
            necessity = self._assess_modifier_necessity(word, next_word)
            importance = 0.8 if necessity == 'required' else 0.4
            return '관형어', necessity, importance
        
        return None, 'decorative', 0.1
    
    def _is_main_verb(self, word: str, pos_tags: List[Tuple[str, str]], index: int) -> bool:
        """Determine if a verb is the main predicate"""
        # Simple heuristic: last verb in sentence is usually main verb
        remaining_verbs = [pos for word, pos in pos_tags[index+1:] 
                          if pos in self.predicate_pos.get(self.analyzer_type, [])]
        return len(remaining_verbs) == 0
    
    def _is_descriptive_adverb(self, word: str) -> bool:
        """Check if adverb is purely descriptive (not essential)"""
        descriptive_adverbs = ['매우', '정말', '아주', '너무', '꽤', '상당히', '조금', '약간']
        return word in descriptive_adverbs
    
    def _assess_modifier_necessity(self, modifier: str, noun: str) -> str:
        """Assess whether a modifier is necessary for meaning"""
        # Essential modifiers that specify type/category
        essential_patterns = ['주요', '핵심', '기본', '최초', '최종', '유일한']
        
        if any(pattern in modifier for pattern in essential_patterns):
            return 'required'
        
        # Descriptive modifiers are usually optional
        descriptive_patterns = ['아름다운', '예쁜', '큰', '작은', '빨간', '파란']
        if any(pattern in modifier for pattern in descriptive_patterns):
            return 'optional'
        
        return 'optional'  # Default to optional
    
    def _identify_complex_components(self, components: Dict, pos_tags: List[Tuple[str, str]]) -> Dict:
        """Identify multi-word components and compound structures"""
        
        # Identify compound subjects (A와 B, A 그리고 B)
        components = self._merge_compound_components(components, '주어')
        
        # Identify compound predicates
        components = self._merge_compound_components(components, '서술어')
        
        # Identify phrasal objects
        components = self._merge_phrasal_components(components, '목적어')
        
        return components
    
    def _merge_compound_components(self, components: Dict, component_type: str) -> Dict:
        """Merge compound components (connected by 와/과, 그리고, etc.)"""
        # Implementation for compound component identification
        # This would analyze patterns like "A와 B는" or "크고 작은"
        return components
    
    def _merge_phrasal_components(self, components: Dict, component_type: str) -> Dict:
        """Merge multi-word phrases into single components"""
        # Implementation for phrasal component identification
        return components
    
    def _classify_sentence_role(self, components: Dict, sentence: str) -> str:
        """Classify the role of the sentence in a paragraph"""
        
        # Topic sentence indicators
        topic_indicators = ['이다', '있다', '것이다', '의미한다', '나타낸다']
        if any(indicator in sentence for indicator in topic_indicators):
            if len(components['주어']) > 0:
                return 'topic'
        
        # Supporting detail indicators
        supporting_indicators = ['예를 들어', '또한', '그리고', '따라서']
        if any(indicator in sentence for indicator in supporting_indicators):
            return 'supporting'
        
        # Example indicators
        example_indicators = ['예시', '사례', '경우', '실제로']
        if any(indicator in sentence for indicator in example_indicators):
            return 'example'
        
        # Conclusion indicators  
        conclusion_indicators = ['결론적으로', '따라서', '그러므로', '결국']
        if any(indicator in sentence for indicator in conclusion_indicators):
            return 'conclusion'
        
        return 'supporting'  # Default
    
    def _calculate_importance_score(self, components: Dict, sentence_role: str) -> float:
        """Calculate overall importance of sentence"""
        
        base_score = {
            'topic': 0.9,
            'conclusion': 0.85,
            'supporting': 0.6,
            'example': 0.4,
            'transition': 0.3
        }.get(sentence_role, 0.5)
        
        # Adjust based on component richness
        component_score = 0.0
        for comp_type, comp_list in components.items():
            required_count = len([c for c in comp_list if c.necessity == 'required'])
            component_score += required_count * 0.1
        
        return min(1.0, base_score + component_score)
    
    def _assess_complexity(self, components: Dict, pos_tags: List[Tuple[str, str]]) -> str:
        """Assess grammatical complexity of sentence"""
        
        total_components = sum(len(comp_list) for comp_list in components.values())
        sentence_length = len(pos_tags)
        
        # Simple classification based on components and length
        if total_components <= 3 and sentence_length <= 10:
            return 'simple'
        elif total_components <= 6 and sentence_length <= 20:
            return 'compound'
        else:
            return 'complex'
    
    def _extract_main_concept(self, components: Dict) -> str:
        """Extract the main concept/topic from sentence components"""
        
        # Look for main subject first
        if components['주어']:
            main_subject = components['주어'][0].text
            # Remove particles
            main_concept = re.sub(r'[은는이가을를]$', '', main_subject)
            return main_concept
        
        # Look for important nouns in predicates
        if components['서술어']:
            for predicate in components['서술어']:
                if predicate.importance_score > 0.8:
                    return predicate.text
        
        return "개념 미확인"
    
    def analyze_paragraph(self, paragraph: str) -> List[SentenceAnalysis]:
        """
        Analyze an entire paragraph sentence by sentence.
        
        Args:
            paragraph: Korean paragraph text
            
        Returns:
            List of SentenceAnalysis objects
        """
        
        # Split into sentences
        sentences = self._split_sentences(paragraph)
        
        # Analyze each sentence
        analyses = []
        for sentence in sentences:
            if sentence.strip():
                analysis = self.analyze_sentence(sentence.strip())
                analyses.append(analysis)
        
        # Post-process for paragraph-level relationships
        analyses = self._analyze_paragraph_structure(analyses)
        
        return analyses
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split Korean text into sentences"""
        # Korean sentence boundaries
        boundaries = r'[.!?][\s]+'
        sentences = re.split(boundaries, text)
        
        # Clean empty sentences
        return [s.strip() for s in sentences if s.strip()]
    
    def _analyze_paragraph_structure(self, analyses: List[SentenceAnalysis]) -> List[SentenceAnalysis]:
        """Analyze structural relationships between sentences"""
        
        if not analyses:
            return analyses
        
        # First sentence is often topic sentence
        if len(analyses) > 1:
            analyses[0].sentence_role = 'topic'
            analyses[0].importance_score = max(0.9, analyses[0].importance_score)
        
        # Last sentence might be conclusion
        if len(analyses) > 2:
            last_sentence = analyses[-1]
            conclusion_indicators = ['따라서', '그러므로', '결국', '이렇게']
            if any(indicator in last_sentence.original_text for indicator in conclusion_indicators):
                last_sentence.sentence_role = 'conclusion'
                last_sentence.importance_score = max(0.85, last_sentence.importance_score)
        
        return analyses
    
    def extract_summary_components(self, sentence_analysis: SentenceAnalysis) -> Dict[str, List[str]]:
        """
        Extract components needed for summary writing.
        
        Returns:
            Dictionary with essential, optional, and removable components
        """
        
        essential = []
        optional = []
        removable = []
        
        for comp_type, comp_list in sentence_analysis.components.items():
            for component in comp_list:
                if component.necessity == 'required' and component.importance_score > 0.7:
                    essential.append(component.text)
                elif component.necessity in ['required', 'optional'] and component.importance_score > 0.4:
                    optional.append(component.text)
                else:
                    removable.append(component.text)
        
        return {
            'essential': essential,
            'optional': optional,
            'removable': removable
        }
    
    def generate_learning_hints(self, sentence_analysis: SentenceAnalysis, 
                              user_summary: str) -> List[str]:
        """
        Generate educational hints based on sentence analysis and user attempt.
        
        Args:
            sentence_analysis: Analysis of the original sentence
            user_summary: Student's summary attempt
            
        Returns:
            List of educational hint messages
        """
        
        hints = []
        user_analysis = self.analyze_sentence(user_summary)
        
        # Check for missing essential components
        original_essential = self.extract_summary_components(sentence_analysis)['essential']
        user_essential = self.extract_summary_components(user_analysis)['essential']
        
        missing_components = set(original_essential) - set(user_essential)
        if missing_components:
            hints.append(f"필수 성분이 빠졌습니다: {', '.join(missing_components)}")
        
        # Check for unnecessary components
        user_removable = self.extract_summary_components(user_analysis)['removable']
        if user_removable:
            hints.append(f"불필요한 수식어를 제거하세요: {', '.join(user_removable)}")
        
        # Check sentence structure
        if user_analysis.complexity_level == 'complex' and sentence_analysis.complexity_level == 'simple':
            hints.append("문장을 더 간단하게 만들어보세요.")
        
        # Check main concept preservation
        if (user_analysis.main_concept != sentence_analysis.main_concept and 
            sentence_analysis.main_concept != "개념 미확인"):
            hints.append(f"핵심 개념 '{sentence_analysis.main_concept}'이 빠졌습니다.")
        
        return hints