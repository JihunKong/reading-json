"""
Production Monitoring System for Korean Reading Comprehension System
Includes health checks, metrics collection, and alerting
"""

import os
import sys
import time
import psutil
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
import json
import sqlite3
from contextlib import contextmanager
from flask import Flask, request, g
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import logging

from utils.logging_config import get_logger, get_performance_logger
from config.config import get_config

logger = get_logger(__name__)
perf_logger = get_performance_logger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    healthy: bool
    message: str
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricData:
    """Metric data point"""
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class HealthChecker:
    """Health check system for monitoring service health"""
    
    def __init__(self):
        self.checks: Dict[str, Callable[[], HealthCheckResult]] = {}
        self.config = get_config()
    
    def register_check(self, name: str, check_func: Callable[[], HealthCheckResult]):
        """Register a health check function"""
        self.checks[name] = check_func
        logger.info(f"Registered health check: {name}")
    
    def run_check(self, name: str) -> HealthCheckResult:
        """Run a specific health check"""
        if name not in self.checks:
            return HealthCheckResult(
                name=name,
                healthy=False,
                message=f"Health check '{name}' not found",
                duration_ms=0
            )
        
        start_time = time.time()
        try:
            result = self.checks[name]()
            result.duration_ms = (time.time() - start_time) * 1000
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.exception(f"Health check '{name}' failed")
            return HealthCheckResult(
                name=name,
                healthy=False,
                message=f"Health check failed: {str(e)}",
                duration_ms=duration_ms
            )
    
    def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks"""
        results = {}
        for name in self.checks:
            results[name] = self.run_check(name)
        return results
    
    def get_overall_health(self) -> HealthCheckResult:
        """Get overall system health"""
        results = self.run_all_checks()
        
        healthy = all(result.healthy for result in results.values())
        failed_checks = [name for name, result in results.items() if not result.healthy]
        
        if healthy:
            message = "All health checks passed"
        else:
            message = f"Failed checks: {', '.join(failed_checks)}"
        
        total_duration = sum(result.duration_ms for result in results.values())
        
        return HealthCheckResult(
            name="overall",
            healthy=healthy,
            message=message,
            duration_ms=total_duration,
            metadata={"individual_results": results}
        )


class MetricsCollector:
    """Collects and exports application metrics"""
    
    def __init__(self):
        self.config = get_config()
        self._setup_prometheus_metrics()
        self._custom_metrics: List[MetricData] = []
        self._metrics_lock = threading.Lock()
    
    def _setup_prometheus_metrics(self):
        """Setup Prometheus metrics"""
        # Request metrics
        self.request_count = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )
        
        self.request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint']
        )
        
        # System metrics
        self.system_cpu_usage = Gauge(
            'system_cpu_usage_percent',
            'System CPU usage percentage'
        )
        
        self.system_memory_usage = Gauge(
            'system_memory_usage_bytes',
            'System memory usage in bytes'
        )
        
        self.system_disk_usage = Gauge(
            'system_disk_usage_percent',
            'System disk usage percentage'
        )
        
        # Application metrics
        self.active_users = Gauge(
            'active_users_total',
            'Number of active users'
        )
        
        self.questions_generated = Counter(
            'questions_generated_total',
            'Total questions generated',
            ['type', 'difficulty']
        )
        
        self.questions_answered = Counter(
            'questions_answered_total',
            'Total questions answered',
            ['correct', 'type']
        )
        
        self.grading_duration = Histogram(
            'grading_duration_seconds',
            'Grading operation duration',
            ['type']
        )
        
        # Database metrics
        self.db_connections = Gauge(
            'database_connections_active',
            'Active database connections'
        )
        
        self.db_query_duration = Histogram(
            'database_query_duration_seconds',
            'Database query duration',
            ['operation']
        )
        
        # Cache metrics
        self.cache_hits = Counter(
            'cache_hits_total',
            'Cache hits',
            ['cache_name']
        )
        
        self.cache_misses = Counter(
            'cache_misses_total',
            'Cache misses',
            ['cache_name']
        )
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        self.request_count.labels(
            method=method,
            endpoint=endpoint,
            status=str(status_code)
        ).inc()
        
        self.request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_question_generated(self, question_type: str, difficulty: str):
        """Record question generation metric"""
        self.questions_generated.labels(
            type=question_type,
            difficulty=difficulty
        ).inc()
    
    def record_question_answered(self, correct: bool, question_type: str):
        """Record question answering metric"""
        self.questions_answered.labels(
            correct='true' if correct else 'false',
            type=question_type
        ).inc()
    
    def record_grading_duration(self, grading_type: str, duration: float):
        """Record grading operation duration"""
        self.grading_duration.labels(type=grading_type).observe(duration)
    
    def record_custom_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record custom metric"""
        with self._metrics_lock:
            self._custom_metrics.append(MetricData(
                name=name,
                value=value,
                labels=labels or {}
            ))
    
    def update_system_metrics(self):
        """Update system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu_usage.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.system_memory_usage.set(memory.used)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.system_disk_usage.set(disk_percent)
            
        except Exception as e:
            logger.warning(f"Failed to update system metrics: {e}")
    
    def get_prometheus_metrics(self) -> str:
        """Get Prometheus formatted metrics"""
        self.update_system_metrics()
        return generate_latest()


class SystemMonitor:
    """Main system monitoring class"""
    
    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        self.config = get_config()
        self.health_checker = HealthChecker()
        self.metrics_collector = MetricsCollector()
        self._monitoring_thread = None
        self._running = False
        
        # Setup default health checks
        self._setup_default_health_checks()
        
        if app:
            self._setup_flask_monitoring(app)
    
    def _setup_default_health_checks(self):
        """Setup default health checks"""
        self.health_checker.register_check("database", self._check_database)
        self.health_checker.register_check("redis", self._check_redis)
        self.health_checker.register_check("rabbitmq", self._check_rabbitmq)
        self.health_checker.register_check("disk_space", self._check_disk_space)
        self.health_checker.register_check("memory", self._check_memory)
    
    def _check_database(self) -> HealthCheckResult:
        """Check database connectivity"""
        try:
            import psycopg2
            from config.secrets import get_database_url
            
            conn = psycopg2.connect(get_database_url())
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            
            return HealthCheckResult(
                name="database",
                healthy=True,
                message="Database connection successful",
                duration_ms=0
            )
        except Exception as e:
            return HealthCheckResult(
                name="database",
                healthy=False,
                message=f"Database connection failed: {str(e)}",
                duration_ms=0
            )
    
    def _check_redis(self) -> HealthCheckResult:
        """Check Redis connectivity"""
        try:
            import redis
            from config.secrets import get_redis_url
            
            r = redis.from_url(get_redis_url())
            r.ping()
            
            return HealthCheckResult(
                name="redis",
                healthy=True,
                message="Redis connection successful",
                duration_ms=0
            )
        except Exception as e:
            return HealthCheckResult(
                name="redis",
                healthy=False,
                message=f"Redis connection failed: {str(e)}",
                duration_ms=0
            )
    
    def _check_rabbitmq(self) -> HealthCheckResult:
        """Check RabbitMQ connectivity"""
        try:
            import pika
            from config.secrets import get_rabbitmq_url
            
            connection = pika.BlockingConnection(pika.URLParameters(get_rabbitmq_url()))
            connection.close()
            
            return HealthCheckResult(
                name="rabbitmq",
                healthy=True,
                message="RabbitMQ connection successful",
                duration_ms=0
            )
        except Exception as e:
            return HealthCheckResult(
                name="rabbitmq",
                healthy=False,
                message=f"RabbitMQ connection failed: {str(e)}",
                duration_ms=0
            )
    
    def _check_disk_space(self) -> HealthCheckResult:
        """Check disk space"""
        try:
            disk = psutil.disk_usage('/')
            usage_percent = (disk.used / disk.total) * 100
            
            if usage_percent > 90:
                return HealthCheckResult(
                    name="disk_space",
                    healthy=False,
                    message=f"Disk usage critical: {usage_percent:.1f}%",
                    duration_ms=0,
                    metadata={"usage_percent": usage_percent}
                )
            elif usage_percent > 80:
                return HealthCheckResult(
                    name="disk_space",
                    healthy=True,
                    message=f"Disk usage warning: {usage_percent:.1f}%",
                    duration_ms=0,
                    metadata={"usage_percent": usage_percent}
                )
            else:
                return HealthCheckResult(
                    name="disk_space",
                    healthy=True,
                    message=f"Disk usage normal: {usage_percent:.1f}%",
                    duration_ms=0,
                    metadata={"usage_percent": usage_percent}
                )
        except Exception as e:
            return HealthCheckResult(
                name="disk_space",
                healthy=False,
                message=f"Failed to check disk space: {str(e)}",
                duration_ms=0
            )
    
    def _check_memory(self) -> HealthCheckResult:
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            usage_percent = memory.percent
            
            if usage_percent > 90:
                return HealthCheckResult(
                    name="memory",
                    healthy=False,
                    message=f"Memory usage critical: {usage_percent:.1f}%",
                    duration_ms=0,
                    metadata={"usage_percent": usage_percent}
                )
            elif usage_percent > 80:
                return HealthCheckResult(
                    name="memory",
                    healthy=True,
                    message=f"Memory usage warning: {usage_percent:.1f}%",
                    duration_ms=0,
                    metadata={"usage_percent": usage_percent}
                )
            else:
                return HealthCheckResult(
                    name="memory",
                    healthy=True,
                    message=f"Memory usage normal: {usage_percent:.1f}%",
                    duration_ms=0,
                    metadata={"usage_percent": usage_percent}
                )
        except Exception as e:
            return HealthCheckResult(
                name="memory",
                healthy=False,
                message=f"Failed to check memory: {str(e)}",
                duration_ms=0
            )
    
    def _setup_flask_monitoring(self, app: Flask):
        """Setup Flask request monitoring"""
        @app.before_request
        def before_request():
            g.start_time = time.time()
        
        @app.after_request
        def after_request(response):
            if hasattr(g, 'start_time'):
                duration = time.time() - g.start_time
                
                self.metrics_collector.record_request(
                    method=request.method,
                    endpoint=request.endpoint or 'unknown',
                    status_code=response.status_code,
                    duration=duration
                )
                
                perf_logger.log_timing(
                    f"request_{request.method}_{request.endpoint}",
                    duration,
                    status_code=response.status_code
                )
            
            return response
        
        # Add health check endpoint
        @app.route('/health')
        def health_check():
            result = self.health_checker.get_overall_health()
            status_code = 200 if result.healthy else 503
            
            return {
                'status': 'healthy' if result.healthy else 'unhealthy',
                'timestamp': result.timestamp.isoformat(),
                'duration_ms': result.duration_ms,
                'message': result.message,
                'checks': {
                    name: {
                        'healthy': check.healthy,
                        'message': check.message,
                        'duration_ms': check.duration_ms
                    }
                    for name, check in result.metadata.get('individual_results', {}).items()
                }
            }, status_code
        
        # Add metrics endpoint
        @app.route('/metrics')
        def metrics():
            return self.metrics_collector.get_prometheus_metrics(), 200, {'Content-Type': CONTENT_TYPE_LATEST}
    
    def start_monitoring(self):
        """Start background monitoring"""
        if self._running:
            return
        
        self._running = True
        self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()
        logger.info("System monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self._running = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        logger.info("System monitoring stopped")
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self._running:
            try:
                # Update system metrics
                self.metrics_collector.update_system_metrics()
                
                # Run health checks
                results = self.health_checker.run_all_checks()
                
                # Log unhealthy checks
                for name, result in results.items():
                    if not result.healthy:
                        logger.error(f"Health check failed: {name} - {result.message}")
                
                # Sleep until next check
                time.sleep(self.config.monitoring.metrics_export_interval)
                
            except Exception as e:
                logger.exception("Error in monitoring loop")
                time.sleep(60)  # Wait a minute before retrying


# Global monitor instance
_monitor = None

def get_monitor() -> SystemMonitor:
    """Get global monitor instance"""
    global _monitor
    if _monitor is None:
        _monitor = SystemMonitor()
    return _monitor


def setup_monitoring(app: Flask) -> SystemMonitor:
    """Setup monitoring for Flask app"""
    global _monitor
    _monitor = SystemMonitor(app)
    return _monitor


@contextmanager
def monitor_operation(operation_name: str, metric_labels: Optional[Dict[str, str]] = None):
    """Context manager for monitoring operations"""
    start_time = time.time()
    monitor = get_monitor()
    
    try:
        yield
        duration = time.time() - start_time
        
        # Record successful operation
        monitor.metrics_collector.record_custom_metric(
            f"{operation_name}_duration_seconds",
            duration,
            labels=metric_labels or {}
        )
        
        monitor.metrics_collector.record_custom_metric(
            f"{operation_name}_total",
            1,
            labels={**(metric_labels or {}), 'status': 'success'}
        )
        
    except Exception as e:
        duration = time.time() - start_time
        
        # Record failed operation
        monitor.metrics_collector.record_custom_metric(
            f"{operation_name}_total",
            1,
            labels={**(metric_labels or {}), 'status': 'error'}
        )
        
        logger.error(f"Operation {operation_name} failed after {duration:.2f}s: {e}")
        raise


if __name__ == "__main__":
    # Test monitoring system
    monitor = get_monitor()
    
    # Test health checks
    health_result = monitor.health_checker.get_overall_health()
    print(f"Overall health: {health_result.healthy} - {health_result.message}")
    
    # Test metrics
    monitor.metrics_collector.record_custom_metric("test_metric", 42.0, {"type": "test"})
    
    # Test operation monitoring
    with monitor_operation("test_operation"):
        time.sleep(0.1)
    
    print("Monitoring test completed")