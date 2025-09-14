#!/usr/bin/env python3
"""
Admission Control System - Phase 3 Week 1
입구단 유량제어를 통한 시스템 안정성 보장

Provides:
- Global admission control (max 200 concurrent requests)
- Session-based admission control (max 100 per session)  
- 429 responses with Retry-After headers
- Request queue management with timeout budget distribution
- Memory-aware request throttling with auto-splitting
"""

import asyncio
import time
import threading
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import logging
from datetime import datetime, timedelta

from .process_manager import log_with_context, process_observer

class AdmissionDecision(Enum):
    ADMIT = "admit"
    REJECT_GLOBAL_LIMIT = "reject_global_limit"
    REJECT_SESSION_LIMIT = "reject_session_limit"
    REJECT_MEMORY_LIMIT = "reject_memory_limit"

@dataclass
class TimeoutBudget:
    """Timeout budget for parser chain with progressive allocation"""
    total_ms: int = 5000
    primary_ms: int = 2500  # UD parser
    secondary_ms: int = 1500  # MeCab parser  
    tertiary_ms: int = 1000  # Heuristic parser
    
    def slice_for_parser(self, parser_type: str) -> int:
        """Get timeout slice for specific parser type"""
        if parser_type == 'ud':
            return self.primary_ms
        elif parser_type == 'mecab':
            return self.secondary_ms
        elif parser_type == 'heuristic':
            return self.tertiary_ms
        return 1000  # Default fallback

@dataclass
class RequestContext:
    """Request context with resource budgets"""
    session_id: str
    correlation_id: str
    text: str
    timestamp: float = field(default_factory=time.time)
    timeout_budget: TimeoutBudget = field(default_factory=TimeoutBudget)
    memory_budget_mb: int = 100
    morpheme_count: Optional[int] = None
    should_split: bool = False
    
    def estimate_morphemes(self) -> int:
        """Quick estimate of morpheme count for memory planning"""
        if self.morpheme_count is None:
            # Rough estimate: Korean text averages ~1.5 morphemes per character
            self.morpheme_count = int(len(self.text) * 1.5)
        return self.morpheme_count
    
    def needs_splitting(self) -> bool:
        """Check if request needs automatic sentence splitting"""
        return self.estimate_morphemes() > 2000

class AdmissionController:
    """
    Dual-level admission control with resource budgets
    전역 + 세션별 입구 제어 시스템
    """
    
    def __init__(self, global_limit: int = 200, session_limit: int = 100):
        self.global_limit = global_limit
        self.session_limit = session_limit
        
        # Global semaphore for system-wide concurrency
        self.global_semaphore = asyncio.Semaphore(global_limit)
        
        # Session-based semaphores
        self.session_semaphores: Dict[str, asyncio.Semaphore] = {}
        self.session_lock = threading.Lock()
        
        # Request tracking for metrics
        self.active_requests = 0
        self.total_requests = 0
        self.rejected_requests = defaultdict(int)
        self.session_request_counts = defaultdict(int)
        
        # Request queue depths for monitoring
        self.queue_depths = deque(maxlen=100)  # Last 100 measurements
        self.last_queue_check = time.time()
        
        # Retry-After calculation
        self.retry_estimates = deque(maxlen=20)  # Recent processing times
        
        self.logger = logging.getLogger(__name__)
        log_with_context('info', 'Admission Controller initialized', 'admission_control',
                        global_limit=global_limit, session_limit=session_limit)
    
    def _get_session_semaphore(self, session_id: str) -> asyncio.Semaphore:
        """Get or create session-specific semaphore"""
        with self.session_lock:
            if session_id not in self.session_semaphores:
                self.session_semaphores[session_id] = asyncio.Semaphore(self.session_limit)
            return self.session_semaphores[session_id]
    
    def _calculate_retry_after(self) -> int:
        """Calculate Retry-After header value based on recent processing times"""
        if not self.retry_estimates:
            return 5  # Default 5 seconds
        
        # Use 95th percentile of recent processing times
        sorted_times = sorted(self.retry_estimates)
        p95_index = int(len(sorted_times) * 0.95)
        p95_time = sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1]
        
        # Add buffer and cap at reasonable maximum
        return min(int(p95_time * 1.5), 30)
    
    def _record_processing_time(self, duration_s: float):
        """Record processing time for retry estimation"""
        self.retry_estimates.append(duration_s)
    
    async def try_admit(self, context: RequestContext) -> Tuple[AdmissionDecision, Optional[int]]:
        """
        Try to admit request through dual admission control
        Returns (decision, retry_after_seconds)
        """
        self.total_requests += 1
        
        # Check memory-based throttling first
        if context.needs_splitting():
            log_with_context('info', 'Request needs splitting due to size', 'admission_control',
                           correlation_id=context.correlation_id, 
                           morpheme_count=context.estimate_morphemes())
            context.should_split = True
        
        # Check global capacity
        if self.global_semaphore.locked():
            self.rejected_requests[AdmissionDecision.REJECT_GLOBAL_LIMIT] += 1
            retry_after = self._calculate_retry_after()
            
            log_with_context('warning', 'Request rejected: global limit exceeded', 'admission_control',
                           correlation_id=context.correlation_id,
                           global_active=self.active_requests,
                           retry_after=retry_after)
            
            return AdmissionDecision.REJECT_GLOBAL_LIMIT, retry_after
        
        # Check session capacity
        session_semaphore = self._get_session_semaphore(context.session_id)
        if session_semaphore.locked():
            self.rejected_requests[AdmissionDecision.REJECT_SESSION_LIMIT] += 1
            retry_after = self._calculate_retry_after()
            
            log_with_context('warning', 'Request rejected: session limit exceeded', 'admission_control',
                           correlation_id=context.correlation_id,
                           session_id=context.session_id,
                           retry_after=retry_after)
            
            return AdmissionDecision.REJECT_SESSION_LIMIT, retry_after
        
        # Admit the request
        return AdmissionDecision.ADMIT, None
    
    async def acquire_resources(self, context: RequestContext) -> bool:
        """
        Acquire both global and session resources
        Returns True if successful, False if timed out
        """
        try:
            # Try to acquire global semaphore first
            global_acquired = await asyncio.wait_for(
                self.global_semaphore.acquire(), 
                timeout=1.0  # Quick timeout to avoid blocking
            )
            
            if global_acquired is False:
                return False
            
            # Then acquire session semaphore
            session_semaphore = self._get_session_semaphore(context.session_id)
            session_acquired = await asyncio.wait_for(
                session_semaphore.acquire(),
                timeout=1.0
            )
            
            if session_acquired is False:
                # Release global semaphore if session acquisition failed
                self.global_semaphore.release()
                return False
            
            # Successfully acquired both
            self.active_requests += 1
            self.session_request_counts[context.session_id] += 1
            
            log_with_context('debug', 'Resources acquired', 'admission_control',
                           correlation_id=context.correlation_id,
                           active_global=self.active_requests,
                           active_session=self.session_request_counts[context.session_id])
            
            return True
            
        except asyncio.TimeoutError:
            return False
    
    def release_resources(self, context: RequestContext, duration_s: float):
        """Release acquired resources and record metrics"""
        # Release semaphores
        self.global_semaphore.release()
        session_semaphore = self._get_session_semaphore(context.session_id)
        session_semaphore.release()
        
        # Update counters
        self.active_requests = max(0, self.active_requests - 1)
        self.session_request_counts[context.session_id] = max(
            0, self.session_request_counts[context.session_id] - 1
        )
        
        # Record timing for retry estimation
        self._record_processing_time(duration_s)
        
        log_with_context('debug', 'Resources released', 'admission_control',
                       correlation_id=context.correlation_id,
                       duration_s=duration_s,
                       active_global=self.active_requests)
    
    def get_admission_metrics(self) -> Dict:
        """Get current admission control metrics"""
        current_time = time.time()
        
        # Update queue depth measurements
        if current_time - self.last_queue_check >= 1.0:  # Every second
            queue_depth = self.global_limit - self.global_semaphore._value
            self.queue_depths.append(queue_depth)
            self.last_queue_check = current_time
        
        return {
            'global_active': self.active_requests,
            'global_limit': self.global_limit,
            'global_utilization': self.active_requests / self.global_limit,
            'session_count': len(self.session_semaphores),
            'total_requests': self.total_requests,
            'rejected_global': self.rejected_requests[AdmissionDecision.REJECT_GLOBAL_LIMIT],
            'rejected_session': self.rejected_requests[AdmissionDecision.REJECT_SESSION_LIMIT],
            'rejected_memory': self.rejected_requests[AdmissionDecision.REJECT_MEMORY_LIMIT],
            'rejection_rate': sum(self.rejected_requests.values()) / max(1, self.total_requests),
            'queue_depth_p95': self._calculate_p95_queue_depth(),
            'avg_retry_after': sum(self.retry_estimates) / len(self.retry_estimates) if self.retry_estimates else 0
        }
    
    def _calculate_p95_queue_depth(self) -> float:
        """Calculate 95th percentile queue depth"""
        if not self.queue_depths:
            return 0.0
        sorted_depths = sorted(self.queue_depths)
        p95_index = int(len(sorted_depths) * 0.95)
        return sorted_depths[p95_index] if p95_index < len(sorted_depths) else sorted_depths[-1]
    
    async def cleanup_inactive_sessions(self, inactive_threshold_minutes: int = 30):
        """Clean up session semaphores for inactive sessions"""
        current_time = time.time()
        threshold = timedelta(minutes=inactive_threshold_minutes)
        
        with self.session_lock:
            inactive_sessions = []
            for session_id, semaphore in self.session_semaphores.items():
                # Check if session has no active requests
                if semaphore._value == self.session_limit:  # All permits available
                    # Additional check: session hasn't been used recently
                    # (In production, integrate with session activity tracking)
                    inactive_sessions.append(session_id)
            
            # Clean up inactive sessions
            for session_id in inactive_sessions:
                del self.session_semaphores[session_id]
                if session_id in self.session_request_counts:
                    del self.session_request_counts[session_id]
            
            if inactive_sessions:
                log_with_context('info', f'Cleaned up {len(inactive_sessions)} inactive sessions', 
                               'admission_control')

# Global admission controller instance
admission_controller = AdmissionController()

# Utility functions for Flask integration
async def admit_request(session_id: str, text: str, correlation_id: str = None) -> Tuple[AdmissionDecision, Optional[int]]:
    """Admit a request through admission control"""
    if correlation_id is None:
        correlation_id = process_observer.get_correlation_id()
    
    context = RequestContext(
        session_id=session_id,
        correlation_id=correlation_id,
        text=text
    )
    
    return await admission_controller.try_admit(context)

async def process_with_admission_control(session_id: str, text: str, 
                                       processing_func, correlation_id: str = None):
    """Process request with full admission control lifecycle"""
    if correlation_id is None:
        correlation_id = process_observer.get_correlation_id()
    
    context = RequestContext(
        session_id=session_id,
        correlation_id=correlation_id,
        text=text
    )
    
    # Check admission
    decision, retry_after = await admission_controller.try_admit(context)
    if decision != AdmissionDecision.ADMIT:
        return {
            'error': 'service_unavailable',
            'message': 'Service temporarily unavailable. Please try again.',
            'retry_after': retry_after,
            'reason': decision.value
        }
    
    # Acquire resources
    if not await admission_controller.acquire_resources(context):
        return {
            'error': 'timeout',
            'message': 'Request timed out acquiring resources. Please try again.',
            'retry_after': admission_controller._calculate_retry_after()
        }
    
    start_time = time.time()
    try:
        # Process the request
        result = await processing_func(context)
        return result
        
    finally:
        duration = time.time() - start_time
        admission_controller.release_resources(context, duration)

def get_admission_metrics():
    """Get current admission control metrics"""
    return admission_controller.get_admission_metrics()

if __name__ == "__main__":
    # Test the admission controller
    import asyncio
    
    async def test_admission_control():
        print("🔍 Testing Admission Control System...")
        
        # Test basic admission
        decision, retry_after = await admit_request("test_session", "안녕하세요")
        print(f"Decision: {decision}, Retry after: {retry_after}")
        
        # Test with large text (should trigger splitting)
        large_text = "매우 긴 텍스트입니다. " * 200  # ~2000+ characters
        decision, retry_after = await admit_request("test_session", large_text)
        print(f"Large text decision: {decision}, Retry after: {retry_after}")
        
        # Get metrics
        metrics = get_admission_metrics()
        print(f"Metrics: {metrics}")
        
        print("✅ Admission Control test completed")
    
    asyncio.run(test_admission_control())