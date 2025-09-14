#!/usr/bin/env python3
"""
Memory Management with Auto-splitting - Phase 3 Week 1
메모리 관리 및 자동 문장 분할 시스템

Provides:
- Memory-aware text processing with 100MB hard limit
- Intelligent Korean sentence splitting at 2k morphemes
- Batch processing for large texts
- Memory usage monitoring and enforcement
- Educational context preservation during splits
"""

import re
import tracemalloc
import gc
import psutil
from typing import List, Dict, Optional, Tuple, Iterator
from dataclasses import dataclass, field
from enum import Enum
import logging
import time

from .process_manager import log_with_context, record_error

class MemoryLimitExceeded(Exception):
    """Raised when memory usage exceeds limits"""
    def __init__(self, current_mb: float, limit_mb: int, context: str = ""):
        self.current_mb = current_mb
        self.limit_mb = limit_mb
        super().__init__(f"Memory limit exceeded: {current_mb:.1f}MB > {limit_mb}MB in {context}")

class TextTooLarge(Exception):
    """Raised when text is too large even after splitting"""
    def __init__(self, morpheme_count: int, max_morphemes: int):
        self.morpheme_count = morpheme_count
        self.max_morphemes = max_morphemes
        super().__init__(f"Text too large: {morpheme_count} > {max_morphemes} morphemes")

@dataclass
class TextSegment:
    """A segment of text with metadata for processing"""
    text: str
    segment_id: int
    start_position: int
    end_position: int
    estimated_morphemes: int
    is_sentence_boundary: bool = True
    context: str = ""  # Educational context preserved from original
    
    def __str__(self):
        return f"Segment {self.segment_id}: '{self.text[:50]}...' ({self.estimated_morphemes} morphemes)"

@dataclass
class MemoryUsage:
    """Memory usage tracking data"""
    current_mb: float
    peak_mb: float
    available_mb: float
    process_mb: float
    timestamp: float = field(default_factory=time.time)

class KoreanTextSplitter:
    """
    Intelligent Korean text splitter that preserves educational context
    한국어 교육적 맥락 보존 텍스트 분할기
    """
    
    def __init__(self):
        # Korean sentence ending patterns
        self.sentence_endings = [
            r'[.!?][\s]*',          # Standard punctuation
            r'[다요][\s]*[.!?]?[\s]*',    # Korean verb endings + optional punctuation
            r'[습니다네요][\s]*[.!?]?[\s]*', # Polite endings
            r'[ㄱ-ㅎㅏ-ㅣ가-힣][.!?][\s]*',  # Korean char + punctuation
        ]
        
        # Compile regex patterns for efficiency
        self.sentence_pattern = re.compile('|'.join(self.sentence_endings), re.MULTILINE)
        
        # Educational context markers to preserve
        self.context_markers = {
            'examples': ['예를 들어', '예컨대', '가령'],
            'explanations': ['즉', '다시 말해', '요약하면'],
            'contrasts': ['그러나', '하지만', '반면에'],
            'sequences': ['먼저', '다음으로', '마지막으로', '결과적으로']
        }
    
    def estimate_morphemes(self, text: str) -> int:
        """Quick morpheme count estimation for Korean text"""
        # Rough heuristic: Korean text averages ~1.5 morphemes per character
        # This is much faster than actual morphological analysis
        korean_chars = len(re.findall(r'[가-힣]', text))
        other_chars = len(text) - korean_chars
        return int(korean_chars * 1.5 + other_chars * 0.8)
    
    def find_sentence_boundaries(self, text: str) -> List[int]:
        """Find sentence boundary positions in Korean text"""
        boundaries = [0]  # Always start at position 0
        
        for match in self.sentence_pattern.finditer(text):
            end_pos = match.end()
            boundaries.append(end_pos)
        
        # Ensure we end at the text end
        if boundaries[-1] != len(text):
            boundaries.append(len(text))
        
        return boundaries
    
    def preserve_educational_context(self, text: str, split_position: int) -> Tuple[str, str]:
        """
        Preserve educational context when splitting text
        Split position을 교육적 맥락을 고려하여 조정
        """
        # Look for context markers around the split position
        context_window = 100  # Look 100 chars before and after split
        start_window = max(0, split_position - context_window)
        end_window = min(len(text), split_position + context_window)
        window_text = text[start_window:end_window]
        
        # Find the best split point within the window
        best_split = split_position
        
        # Check for context markers and adjust split accordingly
        for category, markers in self.context_markers.items():
            for marker in markers:
                marker_pos = window_text.find(marker)
                if marker_pos != -1:
                    absolute_pos = start_window + marker_pos
                    # Don't split in the middle of an explanation/example
                    if abs(absolute_pos - split_position) < 50:
                        # Find next sentence boundary after the marker
                        remaining_text = text[absolute_pos:]
                        boundaries = self.find_sentence_boundaries(remaining_text)
                        if len(boundaries) > 1:  # Has at least one sentence boundary
                            best_split = absolute_pos + boundaries[1]
                            break
        
        # Ensure split doesn't exceed text length
        best_split = min(best_split, len(text))
        
        first_part = text[:best_split].strip()
        second_part = text[best_split:].strip()
        
        return first_part, second_part
    
    def split_by_morpheme_count(self, text: str, max_morphemes: int = 2000) -> List[TextSegment]:
        """
        Split text into segments respecting morpheme count limits
        형태소 수 제한을 고려한 텍스트 분할
        """
        if self.estimate_morphemes(text) <= max_morphemes:
            return [TextSegment(
                text=text,
                segment_id=0,
                start_position=0,
                end_position=len(text),
                estimated_morphemes=self.estimate_morphemes(text),
                is_sentence_boundary=True,
                context="original_text"
            )]
        
        segments = []
        remaining_text = text
        segment_id = 0
        global_position = 0
        
        while remaining_text and self.estimate_morphemes(remaining_text) > max_morphemes:
            # Find sentence boundaries
            boundaries = self.find_sentence_boundaries(remaining_text)
            
            # Build up sentences until we approach the morpheme limit
            current_segment = ""
            segment_end = 0
            
            for i in range(len(boundaries) - 1):
                sentence_start = boundaries[i]
                sentence_end = boundaries[i + 1]
                sentence = remaining_text[sentence_start:sentence_end]
                
                test_segment = current_segment + sentence
                test_morphemes = self.estimate_morphemes(test_segment)
                
                if test_morphemes <= max_morphemes:
                    current_segment = test_segment
                    segment_end = sentence_end
                else:
                    # Adding this sentence would exceed limit
                    break
            
            # If no sentences fit, we need to force split
            if not current_segment:
                # Take at least one sentence or force split at character level
                if len(boundaries) >= 2:
                    segment_end = boundaries[1]
                    current_segment = remaining_text[:segment_end]
                else:
                    # Force character-level split as last resort
                    target_length = len(remaining_text) // 2
                    first_part, second_part = self.preserve_educational_context(remaining_text, target_length)
                    current_segment = first_part
                    segment_end = len(first_part)
            
            # Create segment
            segment = TextSegment(
                text=current_segment.strip(),
                segment_id=segment_id,
                start_position=global_position,
                end_position=global_position + segment_end,
                estimated_morphemes=self.estimate_morphemes(current_segment),
                is_sentence_boundary=True,
                context=f"split_segment_{segment_id}"
            )
            
            segments.append(segment)
            
            # Update for next iteration
            remaining_text = remaining_text[segment_end:].strip()
            global_position += segment_end
            segment_id += 1
            
            # Safety check to prevent infinite loops
            if segment_id > 100:  # Maximum 100 segments
                log_with_context('warning', 'Text splitting safety limit reached', 'memory_management',
                               segment_count=segment_id, remaining_morphemes=self.estimate_morphemes(remaining_text))
                break
        
        # Add remaining text as final segment
        if remaining_text:
            segment = TextSegment(
                text=remaining_text,
                segment_id=segment_id,
                start_position=global_position,
                end_position=global_position + len(remaining_text),
                estimated_morphemes=self.estimate_morphemes(remaining_text),
                is_sentence_boundary=True,
                context=f"final_segment_{segment_id}"
            )
            segments.append(segment)
        
        log_with_context('info', 'Text split into segments', 'memory_management',
                        original_length=len(text), segment_count=len(segments),
                        original_morphemes=self.estimate_morphemes(text))
        
        return segments

class MemoryManager:
    """
    Memory management system with auto-splitting and monitoring
    메모리 관리 및 자동 분할 시스템
    """
    
    def __init__(self, memory_limit_mb: int = 100, morpheme_limit: int = 2000):
        self.memory_limit_mb = memory_limit_mb
        self.morpheme_limit = morpheme_limit
        self.splitter = KoreanTextSplitter()
        
        # Memory tracking
        self.current_usage = MemoryUsage(0, 0, 0, 0)
        self.peak_usage = 0.0
        
        # Enable memory tracing
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        
        log_with_context('info', 'Memory Manager initialized', 'memory_management',
                        memory_limit_mb=memory_limit_mb, morpheme_limit=morpheme_limit)
    
    def get_current_memory_usage(self) -> MemoryUsage:
        """Get current memory usage metrics"""
        try:
            # Process memory usage
            process = psutil.Process()
            process_memory = process.memory_info()
            process_mb = process_memory.rss / 1024 / 1024
            
            # System memory
            system_memory = psutil.virtual_memory()
            available_mb = system_memory.available / 1024 / 1024
            
            # Tracemalloc current usage
            if tracemalloc.is_tracing():
                current, peak = tracemalloc.get_traced_memory()
                current_mb = current / 1024 / 1024
                peak_mb = peak / 1024 / 1024
            else:
                current_mb = 0
                peak_mb = 0
            
            self.current_usage = MemoryUsage(
                current_mb=current_mb,
                peak_mb=peak_mb,
                available_mb=available_mb,
                process_mb=process_mb
            )
            
            # Update peak tracking
            self.peak_usage = max(self.peak_usage, current_mb)
            
            return self.current_usage
            
        except Exception as e:
            log_with_context('warning', f'Failed to get memory usage: {e}', 'memory_management')
            return MemoryUsage(0, 0, 0, 0)
    
    def check_memory_limit(self, operation: str = "unknown") -> bool:
        """Check if current memory usage is within limits"""
        usage = self.get_current_memory_usage()
        
        if usage.current_mb > self.memory_limit_mb:
            raise MemoryLimitExceeded(usage.current_mb, self.memory_limit_mb, operation)
        
        # Log warning if approaching limit (80%)
        if usage.current_mb > self.memory_limit_mb * 0.8:
            log_with_context('warning', 'Approaching memory limit', 'memory_management',
                           current_mb=usage.current_mb, limit_mb=self.memory_limit_mb,
                           operation=operation)
        
        return True
    
    def prepare_text_for_processing(self, text: str, correlation_id: str) -> List[TextSegment]:
        """
        Prepare text for processing with memory management
        메모리 관리를 고려한 텍스트 처리 준비
        """
        try:
            self.check_memory_limit("text_preparation")
            
            # Estimate morphemes
            estimated_morphemes = self.splitter.estimate_morphemes(text)
            
            log_with_context('info', 'Preparing text for processing', 'memory_management',
                           correlation_id=correlation_id, text_length=len(text),
                           estimated_morphemes=estimated_morphemes)
            
            # Check if splitting is needed
            if estimated_morphemes <= self.morpheme_limit:
                # Small enough to process as-is
                return [TextSegment(
                    text=text,
                    segment_id=0,
                    start_position=0,
                    end_position=len(text),
                    estimated_morphemes=estimated_morphemes,
                    is_sentence_boundary=True,
                    context="no_split_needed"
                )]
            
            # Split the text
            segments = self.splitter.split_by_morpheme_count(text, self.morpheme_limit)
            
            # Verify no segment exceeds absolute maximum
            max_allowed_morphemes = self.morpheme_limit * 2  # Allow 2x for edge cases
            for segment in segments:
                if segment.estimated_morphemes > max_allowed_morphemes:
                    raise TextTooLarge(segment.estimated_morphemes, max_allowed_morphemes)
            
            log_with_context('info', 'Text prepared for processing', 'memory_management',
                           correlation_id=correlation_id, segment_count=len(segments),
                           avg_morphemes=sum(s.estimated_morphemes for s in segments) / len(segments))
            
            return segments
            
        except Exception as e:
            record_error(e, 'memory_management', correlation_id)
            raise
    
    def process_segments_with_memory_control(self, segments: List[TextSegment], 
                                           processor_func, correlation_id: str) -> List:
        """
        Process segments with memory monitoring and control
        메모리 제어하에서 세그먼트 처리
        """
        results = []
        
        for i, segment in enumerate(segments):
            try:
                # Check memory before processing each segment
                self.check_memory_limit(f"segment_{i}")
                
                log_with_context('debug', f'Processing segment {i+1}/{len(segments)}', 'memory_management',
                               correlation_id=correlation_id, segment_id=segment.segment_id,
                               morpheme_count=segment.estimated_morphemes)
                
                # Process the segment
                result = processor_func(segment.text)
                results.append({
                    'segment_id': segment.segment_id,
                    'result': result,
                    'context': segment.context,
                    'start_position': segment.start_position,
                    'end_position': segment.end_position
                })
                
                # Force garbage collection after processing each segment
                if i % 5 == 0:  # Every 5 segments
                    gc.collect()
                
            except MemoryLimitExceeded:
                log_with_context('error', f'Memory limit exceeded on segment {i}', 'memory_management',
                               correlation_id=correlation_id, segment_id=segment.segment_id)
                # Force cleanup and retry once
                gc.collect()
                try:
                    self.check_memory_limit(f"segment_{i}_retry")
                    result = processor_func(segment.text)
                    results.append({
                        'segment_id': segment.segment_id,
                        'result': result,
                        'context': f"{segment.context}_retry",
                        'start_position': segment.start_position,
                        'end_position': segment.end_position
                    })
                except MemoryLimitExceeded:
                    # Skip this segment if still over limit
                    log_with_context('warning', f'Skipping segment {i} due to memory constraints', 
                                   'memory_management', correlation_id=correlation_id)
                    continue
            
            except Exception as e:
                record_error(e, 'memory_management', correlation_id, 
                           context={'segment_id': segment.segment_id, 'segment_text': segment.text[:100]})
                continue
        
        log_with_context('info', 'Segment processing completed', 'memory_management',
                        correlation_id=correlation_id, processed_count=len(results),
                        total_segments=len(segments))
        
        return results
    
    def get_memory_metrics(self) -> Dict:
        """Get current memory management metrics"""
        usage = self.get_current_memory_usage()
        
        return {
            'memory_limit_mb': self.memory_limit_mb,
            'current_usage_mb': usage.current_mb,
            'peak_usage_mb': usage.peak_mb,
            'available_mb': usage.available_mb,
            'process_mb': usage.process_mb,
            'utilization_pct': (usage.current_mb / self.memory_limit_mb) * 100,
            'morpheme_limit': self.morpheme_limit,
            'peak_session_mb': self.peak_usage
        }
    
    def cleanup(self):
        """Clean up memory tracking"""
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        gc.collect()

# Global memory manager instance
memory_manager = MemoryManager()

# Utility functions
def prepare_text_with_memory_management(text: str, correlation_id: str) -> List[TextSegment]:
    """Prepare text with memory management"""
    return memory_manager.prepare_text_for_processing(text, correlation_id)

def get_memory_metrics():
    """Get current memory metrics"""
    return memory_manager.get_memory_metrics()

def estimate_morphemes(text: str) -> int:
    """Estimate morpheme count for text"""
    return memory_manager.splitter.estimate_morphemes(text)

if __name__ == "__main__":
    # Test the memory management system
    def test_memory_management():
        print("🔍 Testing Memory Management System...")
        
        # Test small text (no splitting)
        small_text = "안녕하세요. 이것은 작은 텍스트입니다."
        segments = prepare_text_with_memory_management(small_text, "test-001")
        print(f"Small text: {len(segments)} segments")
        
        # Test large text (requires splitting)
        large_text = "이것은 매우 긴 텍스트입니다. " * 500  # Create large text
        segments = prepare_text_with_memory_management(large_text, "test-002")
        print(f"Large text: {len(segments)} segments")
        
        for i, segment in enumerate(segments[:3]):  # Show first 3 segments
            print(f"  Segment {i}: {segment.estimated_morphemes} morphemes")
        
        # Test memory metrics
        metrics = get_memory_metrics()
        print(f"Memory metrics: {metrics}")
        
        print("✅ Memory Management test completed")
    
    test_memory_management()