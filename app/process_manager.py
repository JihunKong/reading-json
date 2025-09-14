#!/usr/bin/env python3
"""
Process Manager with Observability
운영 안정성을 위한 프로세스 관리 및 모니터링

Provides:
- Process lifecycle management using psutil
- Metrics collection (latency, error rates, memory usage)
- Structured logging with correlation IDs
- Health check endpoints with readiness/liveness probes
- Circuit breaker patterns for parser failures
"""

import os
import sys
import time
import uuid
import logging
import threading
import traceback
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import json
from collections import defaultdict, deque

try:
    import psutil
except ImportError:
    print("⚠️ psutil not available - installing...")
    os.system("pip install psutil")
    import psutil

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open" # Testing if service recovered

@dataclass
class MetricData:
    """System metrics data"""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    active_threads: int
    error_rate: float = 0.0
    avg_response_time: float = 0.0

@dataclass
class CircuitBreaker:
    """Circuit breaker for external dependencies"""
    name: str
    failure_threshold: int = 5
    recovery_timeout: int = 60
    test_request_timeout: int = 10
    
    # Internal state
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0
    next_attempt: float = 0

class ProcessObserver:
    """Advanced process monitoring and health management"""
    
    def __init__(self, service_name: str = "korean-learning-system"):
        self.service_name = service_name
        self.start_time = time.time()
        self.process = psutil.Process()
        
        # Metrics storage (keep last 300 data points = 5 minutes at 1s intervals)
        self.metrics_history: deque = deque(maxlen=300)
        self.error_history: deque = deque(maxlen=100)  # Last 100 errors
        
        # Circuit breakers for critical dependencies
        self.circuit_breakers: Dict[str, CircuitBreaker] = {
            'korean_analyzer': CircuitBreaker('korean_analyzer', failure_threshold=3),
            'phrase_analyzer': CircuitBreaker('phrase_analyzer', failure_threshold=3),
            'session_cleanup': CircuitBreaker('session_cleanup', failure_threshold=5)
        }
        
        # Request tracking for rate limiting
        self.request_counts = defaultdict(int)
        self.request_window_start = time.time()
        
        # Health check configuration
        self.health_checks: Dict[str, Callable] = {}
        self.health_status = HealthStatus.HEALTHY
        
        # Structured logging with correlation IDs
        self._setup_logging()
        
        # Background monitoring thread
        self._monitoring_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitoring_active = True
        self._monitoring_thread.start()
        
        self.logger.info(f"🔍 Process Observer initialized for {service_name}")

    def _setup_logging(self):
        """Setup structured logging with correlation IDs"""
        # Create custom formatter for structured logs
        class StructuredFormatter(logging.Formatter):
            def format(self, record):
                log_data = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'service': 'korean-learning-system',
                    'level': record.levelname,
                    'message': record.getMessage(),
                    'correlation_id': getattr(record, 'correlation_id', None),
                    'component': getattr(record, 'component', 'unknown'),
                    'pid': os.getpid(),
                    'thread': threading.current_thread().name
                }
                
                if record.exc_info:
                    log_data['exception'] = traceback.format_exception(*record.exc_info)
                
                return json.dumps(log_data, ensure_ascii=False)
        
        # Setup logger
        self.logger = logging.getLogger(f'{self.service_name}.observer')
        self.logger.setLevel(logging.INFO)
        
        # Console handler with structured format
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)

    def get_correlation_id(self) -> str:
        """Generate correlation ID for request tracking"""
        return str(uuid.uuid4())[:8]

    def log_with_context(self, level: str, message: str, component: str = "system", 
                        correlation_id: str = None, **kwargs):
        """Log with structured context"""
        extra = {
            'component': component,
            'correlation_id': correlation_id or self.get_correlation_id(),
            **kwargs
        }
        getattr(self.logger, level.lower())(message, extra=extra)

    def collect_metrics(self) -> MetricData:
        """Collect current system metrics"""
        try:
            # CPU and memory usage
            cpu_percent = self.process.cpu_percent()
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            memory_percent = self.process.memory_percent()
            
            # Thread count
            active_threads = threading.active_count()
            
            # Calculate error rate from recent errors
            current_time = time.time()
            recent_errors = [
                err for err in self.error_history 
                if current_time - err.get('timestamp', 0) < 60  # Last minute
            ]
            error_rate = len(recent_errors) / 60.0  # Errors per second
            
            # Calculate average response time (mock for now - would integrate with actual request tracking)
            avg_response_time = self._calculate_avg_response_time()
            
            return MetricData(
                timestamp=current_time,
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                memory_percent=memory_percent,
                active_threads=active_threads,
                error_rate=error_rate,
                avg_response_time=avg_response_time
            )
        except Exception as e:
            self.log_with_context('error', f"Failed to collect metrics: {e}", 'metrics')
            # Return safe defaults
            return MetricData(
                timestamp=time.time(),
                cpu_percent=0.0,
                memory_mb=0.0,
                memory_percent=0.0,
                active_threads=1,
                error_rate=0.0,
                avg_response_time=0.0
            )

    def _calculate_avg_response_time(self) -> float:
        """Calculate average response time from recent requests"""
        # Mock implementation - in production, integrate with actual request timing
        return 0.15  # 150ms average

    def record_error(self, error: Exception, component: str = "unknown", 
                    correlation_id: str = None, context: Dict = None):
        """Record an error with context"""
        error_data = {
            'timestamp': time.time(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'component': component,
            'correlation_id': correlation_id or self.get_correlation_id(),
            'context': context or {},
            'stack_trace': traceback.format_exc() if sys.exc_info()[0] else None
        }
        
        self.error_history.append(error_data)
        
        # Log the error
        self.log_with_context(
            'error', 
            f"Error in {component}: {str(error)}", 
            component,
            correlation_id,
            error_type=type(error).__name__,
            context=context
        )

    def check_circuit_breaker(self, service_name: str) -> bool:
        """Check if circuit breaker allows requests"""
        if service_name not in self.circuit_breakers:
            return True
            
        breaker = self.circuit_breakers[service_name]
        current_time = time.time()
        
        if breaker.state == CircuitState.CLOSED:
            return True
        elif breaker.state == CircuitState.OPEN:
            if current_time >= breaker.next_attempt:
                breaker.state = CircuitState.HALF_OPEN
                self.log_with_context('info', f"Circuit breaker {service_name} entering HALF_OPEN", 'circuit_breaker')
                return True
            return False
        elif breaker.state == CircuitState.HALF_OPEN:
            return True
            
        return False

    def record_circuit_success(self, service_name: str):
        """Record successful operation for circuit breaker"""
        if service_name not in self.circuit_breakers:
            return
            
        breaker = self.circuit_breakers[service_name]
        breaker.failure_count = 0
        
        if breaker.state == CircuitState.HALF_OPEN:
            breaker.state = CircuitState.CLOSED
            self.log_with_context('info', f"Circuit breaker {service_name} recovered to CLOSED", 'circuit_breaker')

    def record_circuit_failure(self, service_name: str):
        """Record failed operation for circuit breaker"""
        if service_name not in self.circuit_breakers:
            return
            
        breaker = self.circuit_breakers[service_name]
        breaker.failure_count += 1
        breaker.last_failure_time = time.time()
        
        if breaker.failure_count >= breaker.failure_threshold:
            breaker.state = CircuitState.OPEN
            breaker.next_attempt = time.time() + breaker.recovery_timeout
            self.log_with_context('warning', f"Circuit breaker {service_name} opened due to failures", 'circuit_breaker')

    def register_health_check(self, name: str, check_func: Callable[[], bool]):
        """Register a health check function"""
        self.health_checks[name] = check_func
        self.log_with_context('info', f"Registered health check: {name}", 'health')

    def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks and return results"""
        results = {}
        overall_healthy = True
        
        for name, check_func in self.health_checks.items():
            try:
                start_time = time.time()
                is_healthy = check_func()
                duration = time.time() - start_time
                
                results[name] = {
                    'status': 'pass' if is_healthy else 'fail',
                    'duration': duration,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                if not is_healthy:
                    overall_healthy = False
                    
            except Exception as e:
                results[name] = {
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
                overall_healthy = False
                self.record_error(e, f'health_check_{name}')
        
        # Update overall health status
        if overall_healthy:
            self.health_status = HealthStatus.HEALTHY
        else:
            # Determine degraded vs unhealthy based on failed checks
            failed_checks = sum(1 for r in results.values() if r['status'] != 'pass')
            if failed_checks <= len(results) // 2:
                self.health_status = HealthStatus.DEGRADED
            else:
                self.health_status = HealthStatus.UNHEALTHY
        
        return results

    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report"""
        current_metrics = self.collect_metrics()
        health_checks = self.run_health_checks()
        uptime = time.time() - self.start_time
        
        # Circuit breaker status
        circuit_status = {}
        for name, breaker in self.circuit_breakers.items():
            circuit_status[name] = {
                'state': breaker.state.value,
                'failure_count': breaker.failure_count,
                'last_failure': breaker.last_failure_time
            }
        
        return {
            'service': self.service_name,
            'status': self.health_status.value,
            'uptime_seconds': uptime,
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': {
                'cpu_percent': current_metrics.cpu_percent,
                'memory_mb': current_metrics.memory_mb,
                'memory_percent': current_metrics.memory_percent,
                'active_threads': current_metrics.active_threads,
                'error_rate': current_metrics.error_rate,
                'avg_response_time': current_metrics.avg_response_time
            },
            'health_checks': health_checks,
            'circuit_breakers': circuit_status,
            'recent_errors': list(self.error_history)[-5:]  # Last 5 errors
        }

    def _monitor_loop(self):
        """Background monitoring loop"""
        while self._monitoring_active:
            try:
                # Collect metrics
                metrics = self.collect_metrics()
                self.metrics_history.append(metrics)
                
                # Log high-level metrics every 60 seconds
                if len(self.metrics_history) % 60 == 0:
                    self.log_with_context(
                        'info',
                        f"System metrics: CPU {metrics.cpu_percent:.1f}%, "
                        f"Memory {metrics.memory_mb:.1f}MB ({metrics.memory_percent:.1f}%), "
                        f"Threads {metrics.active_threads}, "
                        f"Error rate {metrics.error_rate:.3f}/s",
                        'monitoring'
                    )
                
                # Check for critical conditions
                if metrics.memory_percent > 90:
                    self.health_status = HealthStatus.CRITICAL
                    self.log_with_context('critical', f"Memory usage critical: {metrics.memory_percent:.1f}%", 'monitoring')
                elif metrics.cpu_percent > 90:
                    self.health_status = HealthStatus.DEGRADED
                    self.log_with_context('warning', f"CPU usage high: {metrics.cpu_percent:.1f}%", 'monitoring')
                
            except Exception as e:
                self.record_error(e, 'monitoring')
            
            time.sleep(1)  # Monitor every second

    def shutdown(self):
        """Graceful shutdown"""
        self.log_with_context('info', "Shutting down process observer", 'system')
        self._monitoring_active = False
        if self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=5)

# Global process observer instance
process_observer = ProcessObserver()

# Utility functions for easy integration
def get_health_status() -> Dict[str, Any]:
    """Get current health status"""
    return process_observer.get_health_report()

def record_error(error: Exception, component: str = "unknown", correlation_id: str = None, context: Dict = None):
    """Record an error with context"""
    process_observer.record_error(error, component, correlation_id, context)

def check_circuit_breaker(service_name: str) -> bool:
    """Check if circuit breaker allows requests"""
    return process_observer.check_circuit_breaker(service_name)

def record_success(service_name: str):
    """Record successful operation"""
    process_observer.record_circuit_success(service_name)

def record_failure(service_name: str):
    """Record failed operation"""
    process_observer.record_circuit_failure(service_name)

def log_with_context(level: str, message: str, component: str = "system", correlation_id: str = None, **kwargs):
    """Log with structured context"""
    process_observer.log_with_context(level, message, component, correlation_id, **kwargs)

# Health check examples
def check_memory_usage() -> bool:
    """Health check for memory usage"""
    try:
        process = psutil.Process()
        memory_percent = process.memory_percent()
        return memory_percent < 80  # Fail if memory usage > 80%
    except:
        return False

def check_disk_space() -> bool:
    """Health check for disk space"""
    try:
        disk_usage = psutil.disk_usage('/')
        free_percent = (disk_usage.free / disk_usage.total) * 100
        return free_percent > 10  # Fail if less than 10% free space
    except:
        return False

# Register default health checks
process_observer.register_health_check('memory', check_memory_usage)
process_observer.register_health_check('disk_space', check_disk_space)

if __name__ == "__main__":
    # Test the process observer
    print("🔍 Testing Process Observer...")
    
    # Simulate some operations
    for i in range(5):
        try:
            # Simulate successful operation
            if check_circuit_breaker('korean_analyzer'):
                record_success('korean_analyzer')
                log_with_context('info', f'Test operation {i} successful', 'test')
            
            time.sleep(1)
            
        except Exception as e:
            record_error(e, 'test')
    
    # Get health report
    health_report = get_health_status()
    print("\n📊 Health Report:")
    print(json.dumps(health_report, indent=2, ensure_ascii=False))
    
    # Shutdown
    process_observer.shutdown()
    print("✅ Process Observer test completed")