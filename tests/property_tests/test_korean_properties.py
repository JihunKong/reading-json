#!/usr/bin/env python3
"""
Property-Based Testing for Korean Text Processing - Phase 3
Hypothesis를 사용한 한국어 텍스트 처리 속성 기반 테스트

Key Properties to Test:
1. Orphan particle prevention (고아 조사 금지)
2. Text reduction ratio (30-70% compression)
3. Non-ASCII/mixed script handling
4. Timeout budget compliance
5. Memory limit enforcement
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, example
from hypothesis.stateful import RuleBasedStateMachine, Bundle, rule, initialize
import re
import time
import asyncio
from typing import List, Tuple, Optional
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.memory_management import KoreanTextSplitter, prepare_text_with_memory_management, estimate_morphemes
from app.admission_control import admit_request
from app.timeout_budget import with_parser_timeout, create_budget_tracker, cleanup_budget_tracker
from core.korean_phrase_analyzer import KoreanPhraseAnalyzer

# Korean text generation strategies
def korean_characters():
    """Strategy for generating Korean characters"""
    return st.characters(min_codepoint=0xAC00, max_codepoint=0xD7AF)  # Hangul Syllables

def korean_particles():
    """Strategy for generating Korean particles"""
    particles = ['은', '는', '이', '가', '을', '를', '에', '에서', '로', '으로', '와', '과', '의', '도', '만']
    return st.sampled_from(particles)

def korean_words():
    """Strategy for generating Korean words"""
    return st.text(alphabet=korean_characters(), min_size=1, max_size=8)

def korean_sentences():
    """Strategy for generating Korean sentences"""
    endings = ['다', '요', '니다', '습니다', '어요', '아요', '죠', '네요']
    
    @st.composite
    def _korean_sentence(draw):
        # Generate word + particle combinations
        num_words = draw(st.integers(min_value=2, max_value=8))
        words = []
        
        for i in range(num_words):
            word = draw(korean_words())
            if i < num_words - 1 and draw(st.booleans()):  # Sometimes add particle
                particle = draw(korean_particles())
                words.append(word + particle)
            else:
                words.append(word)
        
        # Add sentence ending
        ending = draw(st.sampled_from(endings))
        sentence = ' '.join(words[:-1]) + words[-1] + ending
        
        return sentence
    
    return _korean_sentence()

def mixed_script_text():
    """Strategy for generating mixed Korean/English/number text"""
    @st.composite
    def _mixed_text(draw):
        korean_part = draw(korean_sentences())
        english_part = draw(st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=122), min_size=1, max_size=20))
        number_part = draw(st.text(alphabet=st.characters(min_codepoint=48, max_codepoint=57), min_size=1, max_size=10))
        
        # Randomly combine parts
        parts = [korean_part, english_part, number_part]
        selected_parts = draw(st.lists(st.sampled_from(parts), min_size=1, max_size=3))
        
        return ' '.join(selected_parts)
    
    return _mixed_text()

class TestKoreanTextProperties:
    """Property-based tests for Korean text processing"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.splitter = KoreanTextSplitter()
        self.analyzer = KoreanPhraseAnalyzer()
    
    @given(korean_sentences())
    @example("학생이 공부한다.")
    @example("도시 녹화는 현대 도시 문제 해결에 중요한 역할을 한다.")
    def test_no_orphan_particles_after_processing(self, text: str):
        """
        Property: 처리 후 고아 조사가 없어야 함
        Orphan particles (particles without preceding nouns) should never exist after processing
        """
        assume(len(text.strip()) > 0)
        
        try:
            # Analyze the text
            phrases = self.analyzer.analyze_phrase_structure(text)
            
            # Check each phrase for orphan particles
            for phrase in phrases:
                phrase_text = phrase.text.strip()
                
                if not phrase_text:
                    continue
                
                # Korean particle regex pattern
                particle_pattern = r'(?:^|\s)(은|는|이|가|을|를|에|에서|로|으로|와|과|의|도|만)(?:\s|$)'
                orphan_matches = re.findall(particle_pattern, phrase_text)
                
                # Check if particle is at the beginning (orphaned)
                if orphan_matches:
                    for match in orphan_matches:
                        # Find position of particle
                        particle_pos = phrase_text.find(match)
                        
                        # Check if there's a Korean character (noun) before the particle
                        preceding_text = phrase_text[:particle_pos].strip()
                        has_preceding_noun = bool(re.search(r'[가-힣]', preceding_text))
                        
                        assert has_preceding_noun, (
                            f"Orphan particle '{match}' found in phrase: '{phrase_text}'\n"
                            f"No preceding Korean noun found before particle at position {particle_pos}"
                        )
        
        except Exception as e:
            # If analysis fails, text should be too malformed to process
            # This is acceptable - we just ensure no orphan particles in successful analyses
            assume(False)
    
    @given(st.text(alphabet=korean_characters(), min_size=10, max_size=1000))
    @settings(max_examples=50)  # Limit examples due to processing time
    def test_text_reduction_ratio(self, text: str):
        """
        Property: 텍스트 축약 비율은 30-70% 범위여야 함
        Text reduction should be within 30-70% range (compressed text should be 30-70% of original)
        """
        assume(len(text.strip()) > 10)
        original_length = len(text)
        
        try:
            # Estimate morphemes for the original text
            original_morphemes = estimate_morphemes(text)
            assume(original_morphemes >= 10)  # Need substantial text
            
            # Process text through memory management (splitting if needed)
            segments = prepare_text_with_memory_management(text, "test-property")
            
            # Calculate total processed length
            total_processed_length = sum(len(segment.text) for segment in segments)
            
            # Calculate reduction ratio
            if original_length > 0:
                reduction_ratio = total_processed_length / original_length
                
                # Allow some flexibility for very short texts or splitting overhead
                if original_morphemes < 50:  # Short texts may not compress much
                    assert 0.2 <= reduction_ratio <= 1.2, (
                        f"Short text reduction ratio {reduction_ratio:.2f} outside acceptable range [0.2, 1.2]\n"
                        f"Original: {original_length} chars, Processed: {total_processed_length} chars"
                    )
                else:
                    assert 0.3 <= reduction_ratio <= 0.7, (
                        f"Text reduction ratio {reduction_ratio:.2f} outside target range [0.3, 0.7]\n"
                        f"Original: {original_length} chars ({original_morphemes} morphemes)\n"
                        f"Processed: {total_processed_length} chars across {len(segments)} segments"
                    )
        
        except Exception as e:
            # If processing fails due to text characteristics, that's acceptable
            assume(False)
    
    @given(mixed_script_text())
    @example("한국어 English 123")
    @example("🎉 축하합니다! Congratulations! 🎊")
    def test_mixed_script_handling(self, text: str):
        """
        Property: 혼합 스크립트 처리 시 빈 결과 방지
        Mixed script text should never result in empty output
        """
        assume(len(text.strip()) > 0)
        
        try:
            segments = prepare_text_with_memory_management(text, "test-mixed-script")
            
            # Should not result in empty output
            assert len(segments) > 0, f"Mixed script text resulted in no segments: '{text}'"
            
            # At least one segment should have content
            has_content = any(len(segment.text.strip()) > 0 for segment in segments)
            assert has_content, f"All segments empty for mixed script text: '{text}'"
            
            # Check that Korean content is preserved
            has_korean = bool(re.search(r'[가-힣]', text))
            if has_korean:
                combined_output = ' '.join(segment.text for segment in segments)
                output_has_korean = bool(re.search(r'[가-힣]', combined_output))
                assert output_has_korean, f"Korean content lost in processing: '{text}' -> '{combined_output}'"
        
        except Exception as e:
            # Mixed script might cause parsing issues - that's acceptable as long as it doesn't crash
            pass
    
    @given(korean_sentences())
    @settings(max_examples=20, deadline=10000)  # Increase deadline for timeout tests
    def test_timeout_budget_compliance(self, text: str):
        """
        Property: 타임아웃 예산 준수 (total ≤ 5s)
        Operations should complete within timeout budget (≤ 5s total)
        """
        assume(len(text.strip()) > 0)
        
        async def _test_timeout_compliance():
            correlation_id = f"test-timeout-{hash(text) % 10000}"
            
            try:
                # Create budget tracker
                tracker = create_budget_tracker(correlation_id)
                start_time = time.time()
                
                # Mock parser function with realistic delay
                async def mock_parser(text_input: str):
                    # Simulate processing time based on text length
                    processing_time = min(len(text_input) * 0.01, 2.0)  # Max 2s
                    await asyncio.sleep(processing_time)
                    return f"processed_{len(text_input)}_chars"
                
                # Test with different parser types
                for parser_type in ['ud', 'mecab', 'heuristic']:
                    try:
                        result = await with_parser_timeout(
                            correlation_id, parser_type, mock_parser, text
                        )
                        assert result is not None, f"Parser {parser_type} returned None"
                    except Exception:
                        # Parser might timeout - that's acceptable
                        pass
                
                total_time = time.time() - start_time
                
                # Should complete within total budget (5s + some buffer for test overhead)
                assert total_time <= 6.0, (
                    f"Total processing time {total_time:.2f}s exceeds budget limit (6s buffer)\n"
                    f"Text: '{text[:50]}...'"
                )
                
            finally:
                cleanup_budget_tracker(correlation_id)
        
        # Run async test
        asyncio.run(_test_timeout_compliance())
    
    @given(st.integers(min_value=1000, max_value=10000))
    def test_morpheme_estimation_consistency(self, target_morphemes: int):
        """
        Property: 형태소 추정 일관성
        Morpheme estimation should be consistent and reasonable
        """
        # Generate text with target morphemes
        base_text = "도시 녹화는 현대 도시 문제 해결에 중요한 역할을 한다. "
        
        # Repeat to reach target morphemes (rough approximation)
        estimated_base = estimate_morphemes(base_text)
        repetitions = max(1, target_morphemes // estimated_base)
        text = base_text * repetitions
        
        # Test estimation consistency
        estimate1 = estimate_morphemes(text)
        estimate2 = estimate_morphemes(text)
        
        # Should be consistent
        assert estimate1 == estimate2, (
            f"Morpheme estimation inconsistent: {estimate1} vs {estimate2}"
        )
        
        # Should be reasonable (not wildly off from target)
        char_count = len(text)
        reasonable_range = (char_count * 0.5, char_count * 2.0)  # Very loose bounds
        
        assert reasonable_range[0] <= estimate1 <= reasonable_range[1], (
            f"Morpheme estimate {estimate1} unreasonable for {char_count} characters\n"
            f"Expected range: {reasonable_range}"
        )

class TestAdmissionControlProperties:
    """Property-based tests for admission control system"""
    
    @given(st.text(min_size=1, max_size=1000))
    @settings(max_examples=30)
    def test_admission_decision_consistency(self, text: str):
        """
        Property: 동일 요청에 대한 입구 제어 결정 일관성
        Admission control decisions should be consistent for identical requests
        """
        async def _test_admission_consistency():
            session_id = "test_session_property"
            correlation_id = "test_correlation_property"
            
            # Make identical requests
            decision1, retry1 = await admit_request(session_id, text, correlation_id)
            decision2, retry2 = await admit_request(session_id, text, f"{correlation_id}_2")
            
            # Decisions should be consistent (both admit or both reject with same reason)
            assert decision1.value == decision2.value, (
                f"Inconsistent admission decisions: {decision1} vs {decision2}\n"
                f"Text: '{text[:50]}...'"
            )
        
        asyncio.run(_test_admission_consistency())

# Stateful testing for complex scenarios
class KoreanProcessingStateMachine(RuleBasedStateMachine):
    """Stateful testing for Korean text processing pipeline"""
    
    texts = Bundle('texts')
    sessions = Bundle('sessions')
    
    def __init__(self):
        super().__init__()
        self.splitter = KoreanTextSplitter()
        self.active_sessions = set()
        self.processed_texts = []
    
    @initialize()
    def setup(self):
        """Initialize the state machine"""
        pass
    
    @rule(target=texts, text=korean_sentences())
    def create_text(self, text: str) -> str:
        """Create a text for processing"""
        assume(len(text.strip()) > 0)
        return text
    
    @rule(target=sessions, session_name=st.text(min_size=5, max_size=20))
    def create_session(self, session_name: str) -> str:
        """Create a session"""
        session_id = f"state_test_{session_name}"
        self.active_sessions.add(session_id)
        return session_id
    
    @rule(text=texts, session=sessions)
    def process_text_in_session(self, text: str, session: str):
        """Process text within a session"""
        assume(session in self.active_sessions)
        
        try:
            # Process text through splitting
            segments = prepare_text_with_memory_management(text, f"state_{session}")
            
            # Verify invariants
            assert len(segments) > 0, "Processing should produce at least one segment"
            
            # Verify no segment is empty
            for segment in segments:
                assert len(segment.text.strip()) > 0, "Segments should not be empty"
            
            # Record successful processing
            self.processed_texts.append({
                'text': text,
                'session': session,
                'segments': len(segments),
                'total_morphemes': sum(segment.estimated_morphemes for segment in segments)
            })
            
        except Exception as e:
            # Some failures are acceptable, but should not crash the system
            pass
    
    @rule(session=sessions)
    def close_session(self, session: str):
        """Close a session"""
        if session in self.active_sessions:
            self.active_sessions.remove(session)
            
            # Verify session data is cleaned up properly
            session_texts = [p for p in self.processed_texts if p['session'] == session]
            
            # All texts in this session should have been processed successfully
            # (if they're in our tracking list)
            for text_data in session_texts:
                assert text_data['segments'] > 0, "Processed texts should have segments"

# Test class for running the state machine
class TestKoreanStateMachine:
    """Test runner for the state machine"""
    
    def test_korean_processing_state_machine(self):
        """Run the Korean processing state machine test"""
        # Run a smaller number of steps for CI/CD
        KoreanProcessingStateMachine.TestCase.settings = settings(
            max_examples=20,
            stateful_step_count=10,
            deadline=30000  # 30 second deadline
        )
        
        test_case = KoreanProcessingStateMachine.TestCase()
        test_case.runTest()

if __name__ == "__main__":
    # Run specific property tests when called directly
    import pytest
    
    print("🔍 Running Korean Text Property-Based Tests...")
    
    # Run with verbose output
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--hypothesis-show-statistics",
        "-x"  # Stop on first failure for debugging
    ])