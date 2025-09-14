#!/usr/bin/env python3
"""
Phase 3 Metrics Dashboard - 6 Core Metrics
실시간 메트릭 대시보드: p50/p95, 429 비율, 품질 레벨 믹스, 회로 상태 등

Core Metrics:
1. parser_latency_ms{type} (p50/p95)
2. admissions{accepted|rejected429}
3. quality_level_ratio (dep/morph/word)
4. circuit_state{parser}
5. timeout_budget_exhausted
6. memory_p95

Usage:
    python3 monitoring/metrics_dashboard.py
    Open http://localhost:8080/dashboard
"""

import time
import json
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from flask import Flask, render_template_string, jsonify
import statistics
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.admission_control import get_admission_metrics
from app.timeout_budget import get_budget_metrics
from app.memory_management import get_memory_metrics
from app.process_manager import get_health_status

@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: float
    value: float
    labels: Dict[str, str] = field(default_factory=dict)

class MetricsCollector:
    """Collects and stores metrics for dashboard"""
    
    def __init__(self, retention_minutes: int = 60):
        self.retention_minutes = retention_minutes
        self.retention_seconds = retention_minutes * 60
        
        # Time series data storage (metric_name -> deque of MetricPoint)
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=3600))  # 1 hour at 1s resolution
        
        # Derived metrics cache
        self.derived_metrics = {}
        
        # Collection state
        self.collecting = False
        self.collection_thread = None
        self.collection_interval = 1.0  # Collect every second
        
        print("📊 Metrics Collector initialized")
    
    def start_collection(self):
        """Start background metric collection"""
        if self.collecting:
            return
            
        self.collecting = True
        self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collection_thread.start()
        print("🔄 Started metrics collection")
    
    def stop_collection(self):
        """Stop background metric collection"""
        self.collecting = False
        if self.collection_thread:
            self.collection_thread.join(timeout=2)
        print("⏹️ Stopped metrics collection")
    
    def _collection_loop(self):
        """Background collection loop"""
        while self.collecting:
            try:
                current_time = time.time()
                
                # Collect admission control metrics
                admission_data = get_admission_metrics()
                self._record_metric('admissions_accepted', current_time, 
                                  admission_data['total_requests'] - sum(admission_data[k] for k in admission_data if k.startswith('rejected')))
                self._record_metric('admissions_rejected_global', current_time, admission_data['rejected_global'])
                self._record_metric('admissions_rejected_session', current_time, admission_data['rejected_session'])
                self._record_metric('admission_utilization', current_time, admission_data['global_utilization'])
                self._record_metric('rejection_rate', current_time, admission_data['rejection_rate'])
                
                # Collect timeout budget metrics
                budget_data = get_budget_metrics()
                self._record_metric('active_timeout_trackers', current_time, budget_data['active_trackers'])
                self._record_metric('timeout_budget_exhausted', current_time, budget_data['exhausted_count'])
                self._record_metric('avg_remaining_budget_seconds', current_time, budget_data['avg_remaining_seconds'])
                
                # Collect memory metrics
                memory_data = get_memory_metrics()
                self._record_metric('memory_usage_mb', current_time, memory_data['current_usage_mb'])
                self._record_metric('memory_utilization_pct', current_time, memory_data['utilization_pct'])
                self._record_metric('memory_p95_session_mb', current_time, memory_data.get('peak_session_mb', 0))
                
                # Collect health status
                health_data = get_health_status()
                health_score = self._health_status_to_score(health_data['status'])
                self._record_metric('health_score', current_time, health_score)
                
                # Calculate derived metrics
                self._calculate_derived_metrics()
                
                # Clean old data
                self._cleanup_old_metrics(current_time)
                
                time.sleep(self.collection_interval)
                
            except Exception as e:
                print(f"⚠️ Error in metrics collection: {e}")
                time.sleep(1)  # Brief pause on error
    
    def _record_metric(self, metric_name: str, timestamp: float, value: float, labels: Dict[str, str] = None):
        """Record a single metric point"""
        point = MetricPoint(
            timestamp=timestamp,
            value=value,
            labels=labels or {}
        )
        self.metrics[metric_name].append(point)
    
    def _health_status_to_score(self, status: str) -> float:
        """Convert health status to numeric score"""
        scores = {
            'healthy': 1.0,
            'degraded': 0.7,
            'unhealthy': 0.3,
            'critical': 0.0
        }
        return scores.get(status, 0.5)
    
    def _calculate_derived_metrics(self):
        """Calculate derived metrics like percentiles"""
        current_time = time.time()
        window_seconds = 300  # 5 minute window for percentiles
        
        # Calculate parser latency percentiles (mock data for now - would integrate with actual parser timing)
        # In production, this would come from actual parser instrumentation
        self._record_mock_parser_latencies(current_time)
        
        # Calculate quality level distribution (mock data)
        self._record_mock_quality_distribution(current_time)
        
        # Calculate circuit breaker states (mock data)
        self._record_mock_circuit_states(current_time)
    
    def _record_mock_parser_latencies(self, timestamp: float):
        """Record mock parser latency data (replace with real instrumentation)"""
        import random
        
        # Simulate realistic latency distributions
        parsers = ['ud', 'mecab', 'heuristic']
        base_latencies = {'ud': 800, 'mecab': 150, 'heuristic': 50}  # Base latencies in ms
        
        for parser in parsers:
            # Simulate latency with some variance
            base = base_latencies[parser]
            latency = max(10, random.normalvariate(base, base * 0.3))
            
            self._record_metric(f'parser_latency_ms', timestamp, latency, {'parser': parser})
    
    def _record_mock_quality_distribution(self, timestamp: float):
        """Record mock quality level distribution"""
        import random
        
        # Simulate quality distribution (dep > morph > word)
        total = 100
        dep_ratio = random.uniform(0.6, 0.8)  # 60-80% dep quality
        morph_ratio = random.uniform(0.15, 0.3)  # 15-30% morph quality
        word_ratio = 1.0 - dep_ratio - morph_ratio  # Remainder is word quality
        
        self._record_metric('quality_level_ratio', timestamp, dep_ratio, {'level': 'dep'})
        self._record_metric('quality_level_ratio', timestamp, morph_ratio, {'level': 'morph'})
        self._record_metric('quality_level_ratio', timestamp, max(0, word_ratio), {'level': 'word'})
    
    def _record_mock_circuit_states(self, timestamp: float):
        """Record mock circuit breaker states"""
        import random
        
        parsers = ['ud_parser', 'mecab_parser', 'heuristic_parser']
        states = ['closed', 'open', 'half_open']
        
        for parser in parsers:
            # Most circuits should be closed (healthy)
            if random.random() < 0.9:  # 90% chance of being closed
                state = 'closed'
            else:
                state = random.choice(states)
            
            state_value = {'closed': 1.0, 'half_open': 0.5, 'open': 0.0}[state]
            self._record_metric('circuit_state', timestamp, state_value, {'parser': parser, 'state': state})
    
    def _cleanup_old_metrics(self, current_time: float):
        """Remove metrics older than retention period"""
        cutoff_time = current_time - self.retention_seconds
        
        for metric_name, points in self.metrics.items():
            # Remove old points (deque will maintain maxlen automatically, but this is explicit cleanup)
            while points and points[0].timestamp < cutoff_time:
                points.popleft()
    
    def get_metric_summary(self, metric_name: str, window_minutes: int = 5) -> Dict[str, Any]:
        """Get summary statistics for a metric"""
        if metric_name not in self.metrics:
            return {'error': f'Metric {metric_name} not found'}
        
        points = self.metrics[metric_name]
        if not points:
            return {'error': f'No data for metric {metric_name}'}
        
        # Filter to time window
        current_time = time.time()
        window_start = current_time - (window_minutes * 60)
        
        recent_points = [p for p in points if p.timestamp >= window_start]
        if not recent_points:
            return {'error': f'No recent data for metric {metric_name}'}
        
        values = [p.value for p in recent_points]
        
        return {
            'metric': metric_name,
            'window_minutes': window_minutes,
            'count': len(values),
            'latest': values[-1] if values else 0,
            'min': min(values) if values else 0,
            'max': max(values) if values else 0,
            'avg': statistics.mean(values) if values else 0,
            'p50': statistics.median(values) if values else 0,
            'p95': statistics.quantiles(values, n=20)[18] if len(values) >= 20 else (max(values) if values else 0),
            'p99': statistics.quantiles(values, n=100)[98] if len(values) >= 100 else (max(values) if values else 0),
            'latest_timestamp': recent_points[-1].timestamp if recent_points else 0
        }
    
    def get_parser_latency_percentiles(self, window_minutes: int = 5) -> Dict[str, Dict]:
        """Get parser latency percentiles by parser type"""
        current_time = time.time()
        window_start = current_time - (window_minutes * 60)
        
        # Group by parser type
        parser_data = defaultdict(list)
        
        if 'parser_latency_ms' in self.metrics:
            for point in self.metrics['parser_latency_ms']:
                if point.timestamp >= window_start:
                    parser_type = point.labels.get('parser', 'unknown')
                    parser_data[parser_type].append(point.value)
        
        # Calculate percentiles for each parser
        result = {}
        for parser, values in parser_data.items():
            if values:
                result[parser] = {
                    'count': len(values),
                    'p50': statistics.median(values),
                    'p95': statistics.quantiles(values, n=20)[18] if len(values) >= 20 else max(values),
                    'p99': statistics.quantiles(values, n=100)[98] if len(values) >= 100 else max(values),
                    'avg': statistics.mean(values)
                }
        
        return result
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get all data needed for dashboard"""
        
        # Core metrics summaries
        dashboard = {
            'timestamp': datetime.now().isoformat(),
            'metrics': {
                'admission_control': {
                    'utilization': self.get_metric_summary('admission_utilization', 5),
                    'rejection_rate': self.get_metric_summary('rejection_rate', 5),
                    'rejected_global': self.get_metric_summary('admissions_rejected_global', 5),
                    'rejected_session': self.get_metric_summary('admissions_rejected_session', 5)
                },
                'timeout_budget': {
                    'active_trackers': self.get_metric_summary('active_timeout_trackers', 5),
                    'exhausted_count': self.get_metric_summary('timeout_budget_exhausted', 5),
                    'avg_remaining': self.get_metric_summary('avg_remaining_budget_seconds', 5)
                },
                'memory_management': {
                    'usage_mb': self.get_metric_summary('memory_usage_mb', 5),
                    'utilization_pct': self.get_metric_summary('memory_utilization_pct', 5),
                    'p95_session_mb': self.get_metric_summary('memory_p95_session_mb', 5)
                },
                'health': {
                    'score': self.get_metric_summary('health_score', 5)
                }
            },
            'parser_latencies': self.get_parser_latency_percentiles(5),
            'quality_distribution': self._get_quality_distribution(),
            'circuit_states': self._get_circuit_states(),
            'slo_compliance': self._check_slo_compliance()
        }
        
        return dashboard
    
    def _get_quality_distribution(self) -> Dict[str, float]:
        """Get current quality level distribution"""
        if 'quality_level_ratio' not in self.metrics:
            return {}
        
        current_time = time.time()
        window_start = current_time - 60  # Last minute
        
        levels = defaultdict(list)
        for point in self.metrics['quality_level_ratio']:
            if point.timestamp >= window_start:
                level = point.labels.get('level', 'unknown')
                levels[level].append(point.value)
        
        # Get latest values
        result = {}
        for level, values in levels.items():
            if values:
                result[level] = values[-1]  # Latest value
        
        return result
    
    def _get_circuit_states(self) -> Dict[str, str]:
        """Get current circuit breaker states"""
        if 'circuit_state' not in self.metrics:
            return {}
        
        current_time = time.time()
        window_start = current_time - 60  # Last minute
        
        states = {}
        for point in self.metrics['circuit_state']:
            if point.timestamp >= window_start:
                parser = point.labels.get('parser', 'unknown')
                state = point.labels.get('state', 'unknown')
                states[parser] = state
        
        return states
    
    def _check_slo_compliance(self) -> Dict[str, Any]:
        """Check SLO compliance"""
        parser_latencies = self.get_parser_latency_percentiles(5)
        rejection_summary = self.get_metric_summary('rejection_rate', 5)
        memory_summary = self.get_metric_summary('memory_utilization_pct', 5)
        
        # SLO thresholds
        p95_threshold = 800  # ms
        rejection_threshold = 0.01  # 1%
        memory_threshold = 80  # 80%
        
        compliance = {
            'latency_slo': {
                'threshold_ms': p95_threshold,
                'compliant': True,
                'worst_parser': None,
                'worst_p95': 0
            },
            'rejection_slo': {
                'threshold_pct': rejection_threshold * 100,
                'current_pct': (rejection_summary.get('latest', 0) * 100),
                'compliant': rejection_summary.get('latest', 0) <= rejection_threshold
            },
            'memory_slo': {
                'threshold_pct': memory_threshold,
                'current_pct': memory_summary.get('latest', 0),
                'compliant': memory_summary.get('latest', 0) <= memory_threshold
            }
        }
        
        # Check latency SLO for each parser
        for parser, data in parser_latencies.items():
            p95 = data.get('p95', 0)
            if p95 > p95_threshold:
                compliance['latency_slo']['compliant'] = False
                if p95 > compliance['latency_slo']['worst_p95']:
                    compliance['latency_slo']['worst_parser'] = parser
                    compliance['latency_slo']['worst_p95'] = p95
        
        return compliance

# Flask dashboard app
dashboard_app = Flask(__name__)
metrics_collector = MetricsCollector()

# HTML template for dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Phase 3 Metrics Dashboard</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin: 0; padding: 20px; background-color: #f5f5f5; 
        }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;
            text-align: center;
        }
        .metrics-grid { 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px; margin-bottom: 20px;
        }
        .metric-card { 
            background: white; padding: 20px; border-radius: 10px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .metric-title { font-weight: bold; font-size: 1.1em; margin-bottom: 10px; color: #333; }
        .metric-value { font-size: 2em; font-weight: bold; color: #667eea; }
        .metric-unit { font-size: 0.6em; color: #666; }
        .metric-trend { font-size: 0.9em; color: #666; margin-top: 5px; }
        .status-ok { color: #28a745; }
        .status-warning { color: #ffc107; }
        .status-error { color: #dc3545; }
        .slo-section { 
            background: white; padding: 20px; border-radius: 10px; 
            margin-top: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .slo-item { 
            display: flex; justify-content: space-between; align-items: center;
            padding: 10px 0; border-bottom: 1px solid #eee;
        }
        .slo-item:last-child { border-bottom: none; }
        .compliance-badge {
            padding: 5px 10px; border-radius: 15px; color: white; font-size: 0.8em;
        }
        .compliant { background-color: #28a745; }
        .non-compliant { background-color: #dc3545; }
        .quality-bar {
            height: 20px; background: #f0f0f0; border-radius: 10px; overflow: hidden;
            margin: 10px 0; position: relative;
        }
        .quality-segment {
            height: 100%; float: left; line-height: 20px; text-align: center;
            font-size: 0.8em; color: white; font-weight: bold;
        }
        .dep { background-color: #28a745; }
        .morph { background-color: #ffc107; }
        .word { background-color: #dc3545; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Phase 3 Metrics Dashboard</h1>
        <p>Korean Learning System - Real-time Monitoring</p>
        <small>Last updated: {{ data.timestamp }}</small>
    </div>
    
    <div class="metrics-grid">
        <!-- Admission Control -->
        <div class="metric-card">
            <div class="metric-title">🚪 Admission Control</div>
            <div class="metric-value">
                {{ "%.1f"|format(data.metrics.admission_control.utilization.latest * 100) }}
                <span class="metric-unit">% utilization</span>
            </div>
            <div class="metric-trend">
                Rejection Rate: {{ "%.2f"|format(data.metrics.admission_control.rejection_rate.latest * 100) }}%
            </div>
        </div>
        
        <!-- Parser Latencies -->
        <div class="metric-card">
            <div class="metric-title">⏱️ Parser Latencies (P95)</div>
            {% for parser, stats in data.parser_latencies.items() %}
            <div style="margin-bottom: 10px;">
                <strong>{{ parser.upper() }}:</strong> 
                <span class="metric-value" style="font-size: 1.2em;">{{ "%.0f"|format(stats.p95) }}</span>
                <span class="metric-unit">ms</span>
            </div>
            {% endfor %}
        </div>
        
        <!-- Quality Distribution -->
        <div class="metric-card">
            <div class="metric-title">🎯 Quality Levels</div>
            <div class="quality-bar">
                {% set dep_pct = (data.quality_distribution.dep or 0) * 100 %}
                {% set morph_pct = (data.quality_distribution.morph or 0) * 100 %}
                {% set word_pct = (data.quality_distribution.word or 0) * 100 %}
                <div class="quality-segment dep" style="width: {{ dep_pct }}%;">
                    {% if dep_pct > 15 %}DEP {{ "%.0f"|format(dep_pct) }}%{% endif %}
                </div>
                <div class="quality-segment morph" style="width: {{ morph_pct }}%;">
                    {% if morph_pct > 15 %}MORPH {{ "%.0f"|format(morph_pct) }}%{% endif %}
                </div>
                <div class="quality-segment word" style="width: {{ word_pct }}%;">
                    {% if word_pct > 15 %}WORD {{ "%.0f"|format(word_pct) }}%{% endif %}
                </div>
            </div>
        </div>
        
        <!-- Memory Usage -->
        <div class="metric-card">
            <div class="metric-title">💾 Memory Usage</div>
            <div class="metric-value">
                {{ "%.1f"|format(data.metrics.memory_management.utilization_pct.latest) }}
                <span class="metric-unit">%</span>
            </div>
            <div class="metric-trend">
                {{ "%.1f"|format(data.metrics.memory_management.usage_mb.latest) }} MB used
            </div>
        </div>
        
        <!-- Timeout Budget -->
        <div class="metric-card">
            <div class="metric-title">⏰ Timeout Budget</div>
            <div class="metric-value">
                {{ data.metrics.timeout_budget.exhausted_count.latest|int }}
                <span class="metric-unit">exhausted</span>
            </div>
            <div class="metric-trend">
                Active: {{ data.metrics.timeout_budget.active_trackers.latest|int }} trackers
            </div>
        </div>
        
        <!-- Circuit Breakers -->
        <div class="metric-card">
            <div class="metric-title">🔌 Circuit Breakers</div>
            {% for parser, state in data.circuit_states.items() %}
            <div style="margin-bottom: 5px;">
                <strong>{{ parser.replace('_', ' ').title() }}:</strong>
                <span class="status-{{ 'ok' if state == 'closed' else 'warning' if state == 'half_open' else 'error' }}">
                    {{ state.replace('_', ' ').title() }}
                </span>
            </div>
            {% endfor %}
        </div>
    </div>
    
    <!-- SLO Compliance -->
    <div class="slo-section">
        <h2>🎯 SLO Compliance</h2>
        
        <div class="slo-item">
            <span><strong>Latency SLO:</strong> P95 ≤ {{ data.slo_compliance.latency_slo.threshold_ms }}ms</span>
            <span class="compliance-badge {{ 'compliant' if data.slo_compliance.latency_slo.compliant else 'non-compliant' }}">
                {{ 'PASS' if data.slo_compliance.latency_slo.compliant else 'FAIL' }}
            </span>
        </div>
        
        <div class="slo-item">
            <span><strong>Rejection SLO:</strong> Rate ≤ {{ data.slo_compliance.rejection_slo.threshold_pct }}%</span>
            <span class="compliance-badge {{ 'compliant' if data.slo_compliance.rejection_slo.compliant else 'non-compliant' }}">
                {{ 'PASS' if data.slo_compliance.rejection_slo.compliant else 'FAIL' }}
            </span>
        </div>
        
        <div class="slo-item">
            <span><strong>Memory SLO:</strong> Usage ≤ {{ data.slo_compliance.memory_slo.threshold_pct }}%</span>
            <span class="compliance-badge {{ 'compliant' if data.slo_compliance.memory_slo.compliant else 'non-compliant' }}">
                {{ 'PASS' if data.slo_compliance.memory_slo.compliant else 'FAIL' }}
            </span>
        </div>
    </div>
    
    <div style="margin-top: 30px; text-align: center; color: #666; font-size: 0.9em;">
        <p>📊 Real-time monitoring for Korean Learning System Phase 3</p>
        <p>Auto-refresh every 5 seconds | <a href="/api/metrics" style="color: #667eea;">Raw JSON Data</a></p>
    </div>
</body>
</html>
"""

@dashboard_app.route('/')
@dashboard_app.route('/dashboard')
def dashboard():
    """Main dashboard page"""
    try:
        data = metrics_collector.get_dashboard_data()
        return render_template_string(DASHBOARD_HTML, data=data)
    except Exception as e:
        return f"Dashboard Error: {str(e)}", 500

@dashboard_app.route('/api/metrics')
def api_metrics():
    """API endpoint for raw metrics data"""
    try:
        data = metrics_collector.get_dashboard_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_app.route('/api/metric/<metric_name>')
def api_metric_detail(metric_name):
    """Get detailed data for a specific metric"""
    try:
        summary = metrics_collector.get_metric_summary(metric_name)
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_app.route('/health')
def dashboard_health():
    """Dashboard health check"""
    return jsonify({
        'status': 'healthy',
        'collecting': metrics_collector.collecting,
        'metrics_count': len(metrics_collector.metrics),
        'timestamp': datetime.now().isoformat()
    })

def run_dashboard(port: int = 8080):
    """Run the metrics dashboard"""
    print(f"🚀 Starting Phase 3 Metrics Dashboard on port {port}")
    print(f"📊 Dashboard URL: http://localhost:{port}/dashboard")
    print(f"🔗 API URL: http://localhost:{port}/api/metrics")
    
    # Start metrics collection
    metrics_collector.start_collection()
    
    try:
        dashboard_app.run(host='0.0.0.0', port=port, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down dashboard...")
    finally:
        metrics_collector.stop_collection()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Phase 3 Metrics Dashboard')
    parser.add_argument('--port', type=int, default=8080, help='Dashboard port (default: 8080)')
    args = parser.parse_args()
    
    run_dashboard(args.port)