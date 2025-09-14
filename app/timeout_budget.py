#!/usr/bin/env python3
"""
Timeout Budget Distribution System - Phase 3 Week 1
시간 예산 분배를 통한 점진적 타임아웃 관리

Provides:
- Progressive timeout allocation (5s total → 2.5s → 1.5s → 1.0s)
- Context-aware timeout management for parser chain
- Timeout budget tracking and enforcement
- Graceful degradation with remaining budget
"""

import asyncio
import time
import threading
import signal
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from contextlib import asynccontextmanager, contextmanager
from enum import Enum
import logging

from .process_manager import log_with_context

class TimeoutBudgetExhausted(Exception):
    """Raised when timeout budget is completely exhausted"""
    pass

class ParserTimeoutError(Exception):
    """Raised when a specific parser times out"""
    def __init__(self, parser_type: str, allocated_time: float, message: str = ""):
        self.parser_type = parser_type
        self.allocated_time = allocated_time
        super().__init__(f"Parser {parser_type} timed out after {allocated_time}s: {message}")

@dataclass
class BudgetAllocation:
    """Budget allocation for different parser types"""
    total_ms: int = 5000
    primary_ms: int = 2500    # UD parser - most sophisticated
    secondary_ms: int = 1500  # MeCab - fast morphological analysis  
    tertiary_ms: int = 1000   # Heuristic - always fast fallback
    
    def get_allocation(self, parser_type: str) -> int:
        """Get timeout allocation for parser type"""
        allocations = {
            'ud': self.primary_ms,
            'mecab': self.secondary_ms, 
            'heuristic': self.tertiary_ms
        }
        return allocations.get(parser_type, 1000)
    
    def to_seconds(self, parser_type: str) -> float:
        """Get timeout in seconds"""
        return self.get_allocation(parser_type) / 1000.0

@dataclass
class BudgetTracker:
    """Tracks budget usage across parser chain"""
    total_budget_ms: int
    start_time: float = field(default_factory=time.time)
    used_budget_ms: int = 0
    parser_timings: Dict[str, float] = field(default_factory=dict)
    current_parser: Optional[str] = None
    
    def remaining_ms(self) -> int:
        """Calculate remaining budget in milliseconds"""
        elapsed_ms = int((time.time() - self.start_time) * 1000)
        return max(0, self.total_budget_ms - elapsed_ms)
    
    def remaining_seconds(self) -> float:
        """Calculate remaining budget in seconds"""
        return self.remaining_ms() / 1000.0
    
    def is_exhausted(self) -> bool:
        """Check if budget is exhausted"""
        return self.remaining_ms() <= 0
    
    def can_allocate(self, parser_type: str, allocation: BudgetAllocation) -> bool:
        """Check if we can allocate budget for parser"""
        needed_ms = allocation.get_allocation(parser_type)
        return self.remaining_ms() >= needed_ms
    
    def record_parser_start(self, parser_type: str):
        """Record when parser starts"""
        self.current_parser = parser_type
        if parser_type not in self.parser_timings:
            self.parser_timings[parser_type] = time.time()
    
    def record_parser_end(self, parser_type: str):
        """Record when parser ends"""
        if parser_type in self.parser_timings:
            duration = time.time() - self.parser_timings[parser_type]
            self.parser_timings[parser_type] = duration
        self.current_parser = None

class TimeoutBudgetManager:
    """
    Manages timeout budgets with progressive allocation
    시간 예산을 통한 점진적 파서 체인 관리
    """
    
    def __init__(self, default_allocation: Optional[BudgetAllocation] = None):
        self.default_allocation = default_allocation or BudgetAllocation()
        self.active_trackers: Dict[str, BudgetTracker] = {}
        self.tracker_lock = threading.Lock()
        
        log_with_context('info', 'Timeout Budget Manager initialized', 'timeout_budget',
                        total_budget=self.default_allocation.total_ms,
                        primary=self.default_allocation.primary_ms,
                        secondary=self.default_allocation.secondary_ms,
                        tertiary=self.default_allocation.tertiary_ms)
    
    def create_tracker(self, correlation_id: str, 
                      custom_allocation: Optional[BudgetAllocation] = None) -> BudgetTracker:
        """Create a new budget tracker for a request"""
        allocation = custom_allocation or self.default_allocation
        tracker = BudgetTracker(total_budget_ms=allocation.total_ms)
        
        with self.tracker_lock:
            self.active_trackers[correlation_id] = tracker
        
        log_with_context('debug', 'Created timeout budget tracker', 'timeout_budget',
                        correlation_id=correlation_id, total_budget=allocation.total_ms)
        
        return tracker
    
    def get_tracker(self, correlation_id: str) -> Optional[BudgetTracker]:
        """Get existing tracker"""
        with self.tracker_lock:
            return self.active_trackers.get(correlation_id)
    
    def cleanup_tracker(self, correlation_id: str):
        """Clean up finished tracker"""
        with self.tracker_lock:
            tracker = self.active_trackers.pop(correlation_id, None)
            if tracker:
                log_with_context('debug', 'Cleaned up timeout budget tracker', 'timeout_budget',
                               correlation_id=correlation_id, 
                               total_used=int((time.time() - tracker.start_time) * 1000),
                               parser_count=len(tracker.parser_timings))

    @asynccontextmanager
    async def with_timeout_budget(self, correlation_id: str, parser_type: str,
                                 custom_allocation: Optional[BudgetAllocation] = None):
        """Context manager for parser execution with timeout budget"""
        allocation = custom_allocation or self.default_allocation
        tracker = self.get_tracker(correlation_id)
        
        if tracker is None:
            tracker = self.create_tracker(correlation_id, allocation)
        
        # Check if budget is exhausted
        if tracker.is_exhausted():
            raise TimeoutBudgetExhausted(f"Timeout budget exhausted for {correlation_id}")
        
        # Check if we can allocate for this parser
        if not tracker.can_allocate(parser_type, allocation):
            remaining = tracker.remaining_seconds()
            raise ParserTimeoutError(
                parser_type, 
                remaining,
                f"Insufficient budget remaining: {remaining:.2f}s"
            )
        
        # Calculate timeout for this parser
        allocated_seconds = min(
            allocation.to_seconds(parser_type),
            tracker.remaining_seconds()
        )
        
        tracker.record_parser_start(parser_type)
        
        log_with_context('debug', f'Starting parser with budget allocation', 'timeout_budget',
                        correlation_id=correlation_id, parser_type=parser_type,
                        allocated_seconds=allocated_seconds,
                        remaining_budget=tracker.remaining_seconds())
        
        try:
            # Execute with timeout
            async with asyncio.timeout(allocated_seconds):
                yield tracker
                
        except asyncio.TimeoutError:
            log_with_context('warning', f'Parser timed out', 'timeout_budget',
                           correlation_id=correlation_id, parser_type=parser_type,
                           allocated_seconds=allocated_seconds)
            raise ParserTimeoutError(parser_type, allocated_seconds, "Parser execution timed out")
            
        finally:
            tracker.record_parser_end(parser_type)
            
            # Log final timing
            if parser_type in tracker.parser_timings:
                actual_duration = tracker.parser_timings[parser_type]
                log_with_context('debug', f'Parser completed', 'timeout_budget',
                               correlation_id=correlation_id, parser_type=parser_type,
                               actual_duration=actual_duration,
                               allocated_seconds=allocated_seconds,
                               remaining_budget=tracker.remaining_seconds())

    @contextmanager 
    def with_sync_timeout_budget(self, correlation_id: str, parser_type: str,
                                custom_allocation: Optional[BudgetAllocation] = None):
        """Synchronous version using signal.alarm (Unix only)"""
        allocation = custom_allocation or self.default_allocation
        tracker = self.get_tracker(correlation_id)
        
        if tracker is None:
            tracker = self.create_tracker(correlation_id, allocation)
        
        if tracker.is_exhausted():
            raise TimeoutBudgetExhausted(f"Timeout budget exhausted for {correlation_id}")
        
        if not tracker.can_allocate(parser_type, allocation):
            remaining = tracker.remaining_seconds()
            raise ParserTimeoutError(
                parser_type, 
                remaining,
                f"Insufficient budget remaining: {remaining:.2f}s"
            )
        
        allocated_seconds = min(
            allocation.to_seconds(parser_type),
            tracker.remaining_seconds()
        )
        
        tracker.record_parser_start(parser_type)
        
        # Set up signal alarm for timeout (Unix only)
        def timeout_handler(signum, frame):
            raise ParserTimeoutError(parser_type, allocated_seconds, "Parser execution timed out")
        
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(allocated_seconds) + 1)  # Add 1 second buffer
        
        try:
            yield tracker
            
        finally:
            # Clean up signal
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
            
            tracker.record_parser_end(parser_type)
            
            if parser_type in tracker.parser_timings:
                actual_duration = tracker.parser_timings[parser_type]
                log_with_context('debug', f'Sync parser completed', 'timeout_budget',
                               correlation_id=correlation_id, parser_type=parser_type,
                               actual_duration=actual_duration,
                               allocated_seconds=allocated_seconds)

    def get_budget_metrics(self) -> Dict[str, Any]:
        """Get current budget management metrics"""
        with self.tracker_lock:
            active_count = len(self.active_trackers)
            
            # Calculate average remaining budget
            avg_remaining = 0.0
            exhausted_count = 0
            
            if self.active_trackers:
                total_remaining = 0.0
                for tracker in self.active_trackers.values():
                    remaining = tracker.remaining_seconds()
                    total_remaining += remaining
                    if tracker.is_exhausted():
                        exhausted_count += 1
                
                avg_remaining = total_remaining / len(self.active_trackers)
            
            return {
                'active_trackers': active_count,
                'avg_remaining_seconds': avg_remaining,
                'exhausted_count': exhausted_count,
                'default_budget_ms': self.default_allocation.total_ms,
                'budget_allocations': {
                    'primary_ms': self.default_allocation.primary_ms,
                    'secondary_ms': self.default_allocation.secondary_ms,
                    'tertiary_ms': self.default_allocation.tertiary_ms
                }
            }

# Global timeout budget manager
timeout_budget_manager = TimeoutBudgetManager()

# Utility functions for easy integration
async def with_parser_timeout(correlation_id: str, parser_type: str, parser_func, *args, **kwargs):
    """Execute parser function with timeout budget"""
    async with timeout_budget_manager.with_timeout_budget(correlation_id, parser_type) as tracker:
        return await parser_func(*args, **kwargs)

def with_sync_parser_timeout(correlation_id: str, parser_type: str, parser_func, *args, **kwargs):
    """Execute synchronous parser function with timeout budget"""
    with timeout_budget_manager.with_sync_timeout_budget(correlation_id, parser_type) as tracker:
        return parser_func(*args, **kwargs)

def create_budget_tracker(correlation_id: str) -> BudgetTracker:
    """Create a new budget tracker"""
    return timeout_budget_manager.create_tracker(correlation_id)

def cleanup_budget_tracker(correlation_id: str):
    """Clean up budget tracker"""
    timeout_budget_manager.cleanup_tracker(correlation_id)

def get_budget_metrics():
    """Get timeout budget metrics"""
    return timeout_budget_manager.get_budget_metrics()

if __name__ == "__main__":
    # Test the timeout budget system
    import asyncio
    
    async def mock_parser(name: str, duration: float):
        """Mock parser for testing"""
        print(f"  Starting {name} parser (expected duration: {duration}s)")
        await asyncio.sleep(duration)
        print(f"  Completed {name} parser")
        return f"{name}_result"
    
    async def test_timeout_budget():
        print("🔍 Testing Timeout Budget System...")
        
        correlation_id = "test-timeout-001"
        
        try:
            # Test normal execution within budget
            result1 = await with_parser_timeout(correlation_id, 'ud', mock_parser, 'UD', 1.0)
            print(f"UD result: {result1}")
            
            result2 = await with_parser_timeout(correlation_id, 'mecab', mock_parser, 'MeCab', 0.8)
            print(f"MeCab result: {result2}")
            
            result3 = await with_parser_timeout(correlation_id, 'heuristic', mock_parser, 'Heuristic', 0.5)
            print(f"Heuristic result: {result3}")
            
        except (TimeoutBudgetExhausted, ParserTimeoutError) as e:
            print(f"Timeout occurred: {e}")
        
        # Test budget exhaustion
        try:
            print("\n🔄 Testing budget exhaustion...")
            correlation_id2 = "test-timeout-002"
            
            # This should exhaust the budget
            await with_parser_timeout(correlation_id2, 'ud', mock_parser, 'Slow UD', 3.0)
            await with_parser_timeout(correlation_id2, 'mecab', mock_parser, 'Slow MeCab', 2.0)  # Should timeout
            
        except (TimeoutBudgetExhausted, ParserTimeoutError) as e:
            print(f"Expected timeout: {e}")
        
        # Get metrics
        metrics = get_budget_metrics()
        print(f"\n📊 Budget Metrics: {metrics}")
        
        # Cleanup
        cleanup_budget_tracker(correlation_id)
        cleanup_budget_tracker(correlation_id2)
        
        print("✅ Timeout Budget test completed")
    
    asyncio.run(test_timeout_budget())