#!/usr/bin/env python3
"""
Locust Load Testing for Phase 3 Resource Management
부하 테스트 시나리오: S1(정상 피크), S2(세션 편향), S3(스파이크), S4(장문 폭탄)

Usage:
    locust -f tests/load_testing/locustfile.py --host=http://localhost:5000
"""

from locust import HttpUser, task, between, events, tag
import random
import time
import json
import logging
from typing import List, Dict

# Test data generator
class TestDataGenerator:
    """Generate test data for different scenarios"""
    
    def __init__(self):
        # Korean sentence templates for generating test data
        self.short_sentences = [
            "학생이 공부한다.",
            "고양이가 잠을 잔다.",
            "비가 많이 온다.",
            "꽃이 예쁘게 핀다.",
            "사람들이 웃고 있다.",
        ]
        
        # Base text for generating long texts
        self.base_long_text = """
        도시 녹화는 현대 도시 문제 해결에 중요한 역할을 한다. 도시의 급속한 발전과 함께 
        환경 문제가 심각해지고 있는 상황에서, 녹지 공간의 확대는 필수적인 과제가 되었다.
        공원과 가로수, 옥상 정원 등 다양한 형태의 녹화 사업은 도시민들에게 쾌적한 
        생활 환경을 제공할 뿐만 아니라, 대기 정화와 소음 감소, 열섬 현상 완화 등의 
        환경적 효과도 가져온다. 또한 도시 녹화는 생태계 복원과 생물 다양성 증진에도 
        기여하며, 시민들의 정신 건강과 삶의 질 향상에 긍정적인 영향을 미친다.
        """
        
        # Generate morpheme-count based texts
        self.text_2k = self._generate_text_with_morphemes(2000)  # ~2k morphemes
        self.text_4k = self._generate_text_with_morphemes(4000)  # ~4k morphemes  
        self.text_6k = self._generate_text_with_morphemes(6000)  # ~6k morphemes
    
    def _generate_text_with_morphemes(self, target_morphemes: int) -> str:
        """Generate text with approximately target morpheme count"""
        # Rough estimate: Korean text averages ~1.5 morphemes per character
        target_chars = int(target_morphemes / 1.5)
        
        text = ""
        while len(text) < target_chars:
            text += self.base_long_text + " "
            
        return text[:target_chars]
    
    def get_short_text(self) -> str:
        """Get random short sentence"""
        return random.choice(self.short_sentences)
    
    def get_medium_text(self) -> str:
        """Get medium length text (~500 morphemes)"""
        return self.base_long_text
    
    def get_long_text(self, morpheme_target: int = 2000) -> str:
        """Get long text for specific morpheme target"""
        if morpheme_target <= 2500:
            return self.text_2k
        elif morpheme_target <= 4500:
            return self.text_4k
        else:
            return self.text_6k

# Global test data generator
test_data = TestDataGenerator()

class BaseKoreanUser(HttpUser):
    """Base class for Korean learning system users"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = f"session_{random.randint(1000, 9999)}"
        self.correlation_id_counter = 0
    
    def get_correlation_id(self) -> str:
        """Generate unique correlation ID"""
        self.correlation_id_counter += 1
        return f"{self.session_id}_{self.correlation_id_counter}"
    
    def summarize_text(self, text: str, expected_status: int = 200, 
                      catch_response: bool = True, name: str = None):
        """Helper method to summarize text with Korean learning system"""
        headers = {
            'X-Session-ID': self.session_id,
            'X-Correlation-ID': self.get_correlation_id(),
            'Content-Type': 'application/json'
        }
        
        payload = {
            'text': text,
            'mode': 'phrase_analysis',
            'educational_level': 'middle'
        }
        
        with self.client.post(
            '/api/summarize',
            json=payload,
            headers=headers,
            catch_response=catch_response,
            name=name or f"summarize_{len(text)}_chars"
        ) as response:
            
            if catch_response:
                if response.status_code == expected_status:
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            if not data.get('success', False):
                                response.failure(f"API returned success=false: {data.get('message', 'Unknown error')}")
                        except json.JSONDecodeError:
                            response.failure("Invalid JSON response")
                elif response.status_code == 429:
                    # Expected for load testing
                    retry_after = response.headers.get('Retry-After', '5')
                    response.success()  # 429 is expected during load testing
                else:
                    response.failure(f"Unexpected status code: {response.status_code}")
            
            return response

# S1: Normal Peak Load (정상 피크)
class NormalPeakUser(BaseKoreanUser):
    """S1: Normal peak load scenario - 400 users, ramp-up 2min, sustain 8min"""
    
    wait_time = between(1, 3)  # 1-3 seconds between requests
    weight = 3
    
    @task(5)
    @tag("normal", "short")
    def summarize_short_text(self):
        """Process short Korean sentences"""
        text = test_data.get_short_text()
        self.summarize_text(text, name="short_text")
    
    @task(3)
    @tag("normal", "medium")
    def summarize_medium_text(self):
        """Process medium length Korean text"""
        text = test_data.get_medium_text()
        self.summarize_text(text, name="medium_text")
    
    @task(1)
    @tag("normal", "long")
    def summarize_long_text(self):
        """Process long Korean text requiring splitting"""
        text = test_data.get_long_text(2000)
        self.summarize_text(text, name="long_text_2k")
    
    @task(1)
    @tag("health")
    def check_health(self):
        """Check system health during load"""
        with self.client.get('/health', catch_response=True, name="health_check") as response:
            if response.status_code == 200:
                try:
                    health_data = response.json()
                    admission_metrics = health_data.get('admission_control', {})
                    
                    # Log high utilization or rejection rates
                    if admission_metrics.get('global_utilization', 0) > 0.8:
                        print(f"High utilization: {admission_metrics['global_utilization']:.1%}")
                    
                    if admission_metrics.get('rejection_rate', 0) > 0.05:
                        print(f"High rejection rate: {admission_metrics['rejection_rate']:.2%}")
                        
                except json.JSONDecodeError:
                    response.failure("Invalid health check JSON")
            else:
                response.failure(f"Health check failed: {response.status_code}")

# S2: Session Bias (세션 편향 - "한 반 폭주")
class SessionBiasUser(BaseKoreanUser):
    """S2: Session bias scenario - Single session flood"""
    
    wait_time = between(0.1, 0.5)  # Very aggressive load
    weight = 1
    
    def on_start(self):
        # Force all users to use same session to trigger session limits
        self.session_id = "flooded_class_session"
        super().on_start()
    
    @task
    @tag("session_flood", "aggressive")
    def flood_single_session(self):
        """Flood single session to test session-level admission control"""
        text = test_data.get_medium_text()
        # Expect 429s due to session limit (100 concurrent)
        self.summarize_text(text, expected_status=429, name="session_flood")

# S3: Spike Load (스파이크 - 짧은 폭증)
class SpikeUser(BaseKoreanUser):
    """S3: Spike scenario - 0→600 users in 30s"""
    
    wait_time = between(0.05, 0.2)  # Very fast requests
    weight = 2
    
    @task
    @tag("spike", "fast")
    def spike_request(self):
        """Fast requests during spike scenario"""
        text = test_data.get_short_text()
        self.summarize_text(text, name="spike_request")

# S4: Long Text Bomb (장문 폭탄)
class LongTextBombUser(BaseKoreanUser):
    """S4: Long text bomb - Average 6k morpheme texts"""
    
    wait_time = between(2, 5)  # Slower due to processing time
    weight = 1
    
    @task(3)
    @tag("long_text", "splitting")
    def bomb_with_4k_text(self):
        """Send 4k morpheme text requiring splitting"""
        text = test_data.get_long_text(4000)
        self.summarize_text(text, name="bomb_4k_morphemes")
    
    @task(2)
    @tag("long_text", "splitting", "extreme")
    def bomb_with_6k_text(self):
        """Send 6k morpheme text requiring multiple splits"""
        text = test_data.get_long_text(6000)
        self.summarize_text(text, name="bomb_6k_morphemes")
    
    @task(1)
    @tag("long_text", "extreme")
    def bomb_with_8k_text(self):
        """Send very long text to test memory limits"""
        text = test_data.get_long_text(8000)
        self.summarize_text(text, name="bomb_8k_morphemes")

# Custom event handlers for metrics collection
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize test metrics collection"""
    print("🔍 Starting Korean Learning System Load Test")
    print(f"Target host: {environment.host}")
    print("Scenarios:")
    print("  S1: Normal Peak (400 users, 2min ramp, 8min sustain)")
    print("  S2: Session Bias (single session flood)")
    print("  S3: Spike Load (0→600 users in 30s)")
    print("  S4: Long Text Bomb (6k morpheme average)")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Collect final metrics"""
    print("📊 Load Test Completed")
    
    # Log final statistics
    stats = environment.stats.total
    print(f"Total Requests: {stats.num_requests}")
    print(f"Failed Requests: {stats.num_failures}")
    print(f"Failure Rate: {stats.fail_ratio:.2%}")
    print(f"Average Response Time: {stats.avg_response_time:.1f}ms")
    print(f"95th Percentile: {stats.get_response_time_percentile(0.95):.1f}ms")
    print(f"Max Response Time: {stats.max_response_time:.1f}ms")
    print(f"RPS: {stats.total_rps:.1f}")
    
    # Check SLO compliance
    p95_ms = stats.get_response_time_percentile(0.95)
    failure_rate = stats.fail_ratio
    
    print("\n🎯 SLO Compliance Check:")
    print(f"  P95 ≤ 800ms: {'✅ PASS' if p95_ms <= 800 else '❌ FAIL'} ({p95_ms:.1f}ms)")
    print(f"  Failure Rate < 5%: {'✅ PASS' if failure_rate < 0.05 else '❌ FAIL'} ({failure_rate:.2%})")

# Scenario-specific configurations for different test runs
class QuickSmokeTest(BaseKoreanUser):
    """Quick smoke test for CI/CD pipeline"""
    
    wait_time = between(0.5, 1.5)
    weight = 1
    
    @task(5)
    @tag("smoke")
    def smoke_test_basic(self):
        """Basic smoke test"""
        text = test_data.get_short_text()
        self.summarize_text(text, name="smoke_basic")
    
    @task(2)
    @tag("smoke")  
    def smoke_test_with_splitting(self):
        """Smoke test with text splitting"""
        text = test_data.get_long_text(2500)
        self.summarize_text(text, name="smoke_splitting")
    
    @task(1)
    @tag("smoke")
    def smoke_health_check(self):
        """Smoke test health endpoint"""
        self.client.get('/health', name="smoke_health")

# User class weights for different test scenarios
# To run specific scenarios:
# locust -f locustfile.py --tags normal  (S1 only)
# locust -f locustfile.py --tags session_flood  (S2 only)  
# locust -f locustfile.py --tags spike (S3 only)
# locust -f locustfile.py --tags long_text (S4 only)
# locust -f locustfile.py --tags smoke (Quick smoke test)