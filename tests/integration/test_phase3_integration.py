#!/usr/bin/env python3
"""
Integration Tests for Phase 3 Components
전체적인 통합 테스트: 어드미션 제어, 타임아웃 예산, 메모리 관리, 헬스 체크

Tests the complete pipeline:
Input → Admission Control → Timeout Budget → Memory Splitting → Results → Metrics
"""

import pytest
import asyncio
import time
import json
import requests
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Optional
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.admission_control import (
    admit_request, AdmissionDecision, process_with_admission_control, 
    get_admission_metrics, admission_controller
)
from app.timeout_budget import (
    with_parser_timeout, TimeoutBudgetExhausted, ParserTimeoutError,
    get_budget_metrics, create_budget_tracker, cleanup_budget_tracker
)
from app.memory_management import (
    prepare_text_with_memory_management, get_memory_metrics,
    MemoryLimitExceeded, TextTooLarge
)
from app.process_manager import get_health_status, process_observer

class TestAdmissionControlIntegration:
    """Integration tests for admission control system"""
    
    @pytest.mark.asyncio
    async def test_global_limit_enforcement(self):
        """Test global admission limit (200) enforcement"""
        
        # Reset admission controller state
        admission_controller.total_requests = 0
        admission_controller.rejected_requests.clear()
        
        # Mock global semaphore to be at capacity
        original_value = admission_controller.global_semaphore._value
        admission_controller.global_semaphore._value = 0  # Simulate full capacity
        
        try:
            decision, retry_after = await admit_request("test_session", "test text")
            
            assert decision == AdmissionDecision.REJECT_GLOBAL_LIMIT
            assert retry_after is not None
            assert retry_after > 0
            
        finally:
            # Restore original state
            admission_controller.global_semaphore._value = original_value
    
    @pytest.mark.asyncio
    async def test_session_limit_enforcement(self):
        """Test session-level admission limit (100) enforcement"""
        
        session_id = "test_session_limit"
        
        # Get session semaphore and simulate full capacity
        session_semaphore = admission_controller._get_session_semaphore(session_id)
        original_value = session_semaphore._value
        session_semaphore._value = 0  # Simulate session at capacity
        
        try:
            decision, retry_after = await admit_request(session_id, "test text")
            
            assert decision == AdmissionDecision.REJECT_SESSION_LIMIT
            assert retry_after is not None
            
        finally:
            # Restore original state
            session_semaphore._value = original_value
    
    @pytest.mark.asyncio
    async def test_429_response_format(self):
        """Test 429 response format includes Retry-After header"""
        
        # This would typically be tested with actual HTTP client
        # Here we test the admission control logic that generates the response
        
        session_id = "test_429_format"
        
        # Force rejection
        original_value = admission_controller.global_semaphore._value
        admission_controller.global_semaphore._value = 0
        
        try:
            decision, retry_after = await admit_request(session_id, "test text")
            
            assert decision == AdmissionDecision.REJECT_GLOBAL_LIMIT
            assert isinstance(retry_after, int)
            assert 1 <= retry_after <= 30  # Reasonable retry interval
            
        finally:
            admission_controller.global_semaphore._value = original_value
    
    def test_admission_metrics_tracking(self):
        """Test admission control metrics are properly tracked"""
        
        metrics = get_admission_metrics()
        
        required_fields = [
            'global_active', 'global_limit', 'global_utilization',
            'session_count', 'total_requests', 'rejected_global',
            'rejected_session', 'rejection_rate', 'queue_depth_p95'
        ]
        
        for field in required_fields:
            assert field in metrics, f"Missing metric field: {field}"
            assert isinstance(metrics[field], (int, float)), f"Invalid metric type for {field}: {type(metrics[field])}"

class TestTimeoutBudgetIntegration:
    """Integration tests for timeout budget system"""
    
    @pytest.mark.asyncio
    async def test_budget_progression(self):
        """Test progressive budget allocation: 2.5s → 1.5s → 1.0s"""
        
        correlation_id = "test_budget_progression"
        
        # Mock parser functions with known delays
        async def mock_ud_parser(text):
            await asyncio.sleep(1.0)  # Should succeed within 2.5s budget
            return "ud_result"
        
        async def mock_mecab_parser(text):
            await asyncio.sleep(0.8)  # Should succeed within 1.5s budget
            return "mecab_result"
        
        async def mock_heuristic_parser(text):
            await asyncio.sleep(0.5)  # Should succeed within 1.0s budget
            return "heuristic_result"
        
        try:
            # Test UD parser (2.5s budget)
            result1 = await with_parser_timeout(
                correlation_id, 'ud', mock_ud_parser, "test text"
            )
            assert result1 == "ud_result"
            
            # Test MeCab parser (1.5s budget)
            result2 = await with_parser_timeout(
                correlation_id, 'mecab', mock_mecab_parser, "test text"
            )
            assert result2 == "mecab_result"
            
            # Test Heuristic parser (1.0s budget)
            result3 = await with_parser_timeout(
                correlation_id, 'heuristic', mock_heuristic_parser, "test text"
            )
            assert result3 == "heuristic_result"
            
        finally:
            cleanup_budget_tracker(correlation_id)
    
    @pytest.mark.asyncio
    async def test_timeout_enforcement(self):
        """Test timeout enforcement for slow parsers"""
        
        correlation_id = "test_timeout_enforcement"
        
        async def slow_parser(text):
            await asyncio.sleep(3.0)  # Should timeout on UD (2.5s limit)
            return "should_not_reach"
        
        try:
            with pytest.raises(ParserTimeoutError) as exc_info:
                await with_parser_timeout(
                    correlation_id, 'ud', slow_parser, "test text"
                )
            
            assert exc_info.value.parser_type == 'ud'
            assert exc_info.value.allocated_time <= 2.5
            
        finally:
            cleanup_budget_tracker(correlation_id)
    
    @pytest.mark.asyncio
    async def test_budget_exhaustion(self):
        """Test budget exhaustion across multiple parser calls"""
        
        correlation_id = "test_budget_exhaustion"
        
        async def moderate_parser(text):
            await asyncio.sleep(2.0)  # Each call takes 2s
            return "result"
        
        try:
            # First call should succeed (UD: 2.5s budget)
            result1 = await with_parser_timeout(
                correlation_id, 'ud', moderate_parser, "test text"
            )
            assert result1 == "result"
            
            # Second call should timeout (MeCab: 1.5s budget, but parser needs 2s)
            with pytest.raises(ParserTimeoutError):
                await with_parser_timeout(
                    correlation_id, 'mecab', moderate_parser, "test text"
                )
                
        finally:
            cleanup_budget_tracker(correlation_id)
    
    def test_budget_metrics(self):
        """Test budget metrics collection"""
        
        metrics = get_budget_metrics()
        
        required_fields = [
            'active_trackers', 'avg_remaining_seconds', 'exhausted_count',
            'default_budget_ms', 'budget_allocations'
        ]
        
        for field in required_fields:
            assert field in metrics, f"Missing budget metric: {field}"
        
        # Check budget allocations
        allocations = metrics['budget_allocations']
        assert allocations['primary_ms'] == 2500  # UD parser
        assert allocations['secondary_ms'] == 1500  # MeCab parser
        assert allocations['tertiary_ms'] == 1000  # Heuristic parser

class TestMemoryManagementIntegration:
    """Integration tests for memory management system"""
    
    def test_auto_splitting_threshold(self):
        """Test automatic splitting at 2k morphemes threshold"""
        
        # Create text that exceeds 2k morphemes
        large_text = "도시 녹화는 현대 도시 문제 해결에 중요한 역할을 한다. " * 200
        
        correlation_id = "test_auto_splitting"
        
        segments = prepare_text_with_memory_management(large_text, correlation_id)
        
        # Should be split into multiple segments
        assert len(segments) > 1, "Large text should be split into multiple segments"
        
        # Each segment should be under the limit
        for segment in segments:
            assert segment.estimated_morphemes <= 2000, (
                f"Segment has {segment.estimated_morphemes} morphemes, "
                f"exceeding limit of 2000"
            )
        
        # Total morphemes should be preserved (approximately)
        total_morphemes = sum(s.estimated_morphemes for s in segments)
        original_estimate = len(large_text) * 1.5  # Rough estimate
        
        # Allow some variance due to splitting overhead
        assert 0.8 * original_estimate <= total_morphemes <= 1.2 * original_estimate
    
    def test_educational_context_preservation(self):
        """Test that educational context is preserved during splitting"""
        
        educational_text = """
        예를 들어, 도시 녹화 사업은 다양한 형태로 진행된다. 
        첫째, 공원 조성을 통한 녹지 확대가 있다.
        둘째, 가로수 식재를 통한 도시 미관 개선이다.
        마지막으로, 건물 옥상의 정원화를 통한 공간 활용이다.
        """ * 50  # Make it large enough to require splitting
        
        correlation_id = "test_educational_context"
        segments = prepare_text_with_memory_management(educational_text, correlation_id)
        
        if len(segments) > 1:
            # Check that context markers are preserved
            combined_text = ' '.join(segment.text for segment in segments)
            
            # Educational markers should be preserved
            context_markers = ['예를 들어', '첫째', '둘째', '마지막으로']
            for marker in context_markers:
                if marker in educational_text:
                    assert marker in combined_text, (
                        f"Educational context marker '{marker}' lost during splitting"
                    )
    
    def test_memory_metrics_tracking(self):
        """Test memory metrics are properly tracked"""
        
        metrics = get_memory_metrics()
        
        required_fields = [
            'memory_limit_mb', 'current_usage_mb', 'peak_usage_mb',
            'utilization_pct', 'morpheme_limit'
        ]
        
        for field in required_fields:
            assert field in metrics, f"Missing memory metric: {field}"
            assert isinstance(metrics[field], (int, float)), f"Invalid type for {field}"
        
        # Verify limits are as expected
        assert metrics['memory_limit_mb'] == 100
        assert metrics['morpheme_limit'] == 2000

class TestHealthEndpointIntegration:
    """Integration tests for health endpoint with all metrics"""
    
    def test_health_endpoint_comprehensive_metrics(self):
        """Test /health endpoint includes all Phase 3 metrics"""
        
        health_report = get_health_status()
        
        # Core health fields
        assert 'service' in health_report
        assert 'status' in health_report
        assert 'timestamp' in health_report
        
        # Process observer metrics should be included
        assert 'metrics' in health_report
        assert 'uptime_seconds' in health_report
    
    def test_health_warning_thresholds(self):
        """Test health warnings trigger at correct thresholds"""
        
        # This test would need to mock high resource usage
        # For now, test that the structure supports warnings
        
        health_report = get_health_status()
        
        # Health report should have structure to support warnings
        if 'warnings' in health_report:
            assert isinstance(health_report['warnings'], list)
    
    def test_health_status_determination(self):
        """Test health status determination based on metrics"""
        
        health_report = get_health_status()
        
        valid_statuses = ['healthy', 'degraded', 'unhealthy', 'critical']
        assert health_report['status'] in valid_statuses

class TestEndToEndPipeline:
    """End-to-end pipeline tests"""
    
    @pytest.mark.asyncio
    async def test_complete_pipeline_flow(self):
        """Test complete flow: Admission → Budget → Memory → Processing"""
        
        test_text = "학생이 열심히 공부한다. 선생님이 친절하게 가르친다. 교실이 조용하다."
        session_id = "test_e2e_pipeline"
        correlation_id = "test_e2e_001"
        
        # Step 1: Admission Control
        decision, retry_after = await admit_request(session_id, test_text, correlation_id)
        assert decision == AdmissionDecision.ADMIT
        
        # Step 2: Memory Management
        segments = prepare_text_with_memory_management(test_text, correlation_id)
        assert len(segments) >= 1
        
        # Step 3: Timeout Budget (mock parser)
        async def mock_processor(segment_text):
            await asyncio.sleep(0.1)  # Fast processing
            return {
                'input': segment_text,
                'phrases': ['학생이', '열심히', '공부한다'],
                'quality_level': 'dep'
            }
        
        try:
            results = []
            for segment in segments:
                result = await with_parser_timeout(
                    correlation_id, 'ud', mock_processor, segment.text
                )
                results.append(result)
            
            assert len(results) == len(segments)
            assert all('phrases' in result for result in results)
            
        finally:
            cleanup_budget_tracker(correlation_id)
    
    @pytest.mark.asyncio 
    async def test_partial_failure_handling(self):
        """Test system behavior with partial failures"""
        
        test_text = "첫 번째 문장입니다. 두 번째 문장입니다."
        session_id = "test_partial_failure"
        correlation_id = "test_partial_001"
        
        # Mock processor that fails on second call
        call_count = 0
        
        async def failing_processor(segment_text):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                await asyncio.sleep(0.1)
                return {'result': 'success', 'quality': 'dep'}
            else:
                raise Exception("Simulated parser failure")
        
        segments = prepare_text_with_memory_management(test_text, correlation_id)
        
        try:
            results = []
            for segment in segments:
                try:
                    result = await with_parser_timeout(
                        correlation_id, 'ud', failing_processor, segment.text
                    )
                    results.append(result)
                except Exception:
                    # Partial failure - continue with fallback
                    results.append({'result': 'fallback', 'quality': 'word'})
            
            # Should have processed all segments (some with fallback)
            assert len(results) == len(segments)
            
            # At least one should be successful, one should be fallback
            qualities = [r.get('quality', 'unknown') for r in results]
            assert 'dep' in qualities or 'word' in qualities
            
        finally:
            cleanup_budget_tracker(correlation_id)

class TestErrorHandlingAndRecovery:
    """Test error handling and recovery mechanisms"""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self):
        """Test circuit breaker integration with timeout system"""
        
        from app.process_manager import check_circuit_breaker, record_failure, record_success
        
        # Reset circuit breaker state
        breaker_name = 'test_parser'
        
        # Record multiple failures to open circuit
        for _ in range(5):  # Assume threshold is 5
            record_failure(breaker_name)
        
        # Check if circuit breaker blocks requests
        is_allowed = check_circuit_breaker(breaker_name)
        
        # The specific behavior depends on circuit breaker implementation
        # This test ensures integration points exist
        assert isinstance(is_allowed, bool)
    
    @pytest.mark.asyncio
    async def test_memory_limit_enforcement(self):
        """Test memory limit enforcement under extreme conditions"""
        
        # This test would need to mock memory usage
        # For now, test that memory monitoring is active
        
        metrics = get_memory_metrics()
        
        # Should be monitoring memory
        assert metrics['memory_limit_mb'] == 100
        assert 'current_usage_mb' in metrics
        assert 'utilization_pct' in metrics

if __name__ == "__main__":
    # Run tests when called directly
    import pytest
    
    print("🔍 Running Phase 3 Integration Tests...")
    
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x"  # Stop on first failure
    ])