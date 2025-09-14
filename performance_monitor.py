#!/usr/bin/env python3
"""
Performance Monitoring and Optimization for Korean Learning System
- Memory usage tracking
- Database query optimization
- Long-running session analysis
- Performance bottleneck identification
"""

import psutil
import sqlite3
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import threading
import gc

class PerformanceMonitor:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or "/Users/jihunkong/reading-json/performance.db"
        self.init_database()
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Performance thresholds
        self.MEMORY_WARNING_THRESHOLD = 80  # % of system memory
        self.QUERY_WARNING_THRESHOLD = 1.0  # seconds
        self.SESSION_WARNING_THRESHOLD = 3600  # 1 hour in seconds
        
        # Set up logging
        logging.basicConfig(
            filename='performance.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def init_database(self):
        """Initialize performance monitoring database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Memory usage table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                rss_mb REAL,
                vms_mb REAL,
                memory_percent REAL,
                available_mb REAL,
                gc_count INTEGER
            )
        """)
        
        # Query performance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                function_name TEXT,
                execution_time REAL,
                parameters TEXT,
                result_size INTEGER,
                error_message TEXT
            )
        """)
        
        # Session performance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                session_start DATETIME,
                session_end DATETIME,
                total_duration REAL,
                phases_completed INTEGER,
                memory_peak_mb REAL,
                task_switches INTEGER,
                warnings TEXT
            )
        """)
        
        # System alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                alert_type TEXT,
                severity TEXT,
                message TEXT,
                resolved BOOLEAN DEFAULT FALSE
            )
        """)
        
        conn.commit()
        conn.close()
        
    def start_monitoring(self, interval_seconds: int = 30):
        """Start background performance monitoring"""
        if self.monitoring_active:
            return False
            
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval_seconds,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logging.info("Performance monitoring started")
        return True
        
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logging.info("Performance monitoring stopped")
        
    def _monitor_loop(self, interval_seconds: int):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect memory metrics
                self._collect_memory_metrics()
                
                # Check for performance issues
                self._check_performance_alerts()
                
                # Sleep for interval
                time.sleep(interval_seconds)
                
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                time.sleep(interval_seconds)
                
    def _collect_memory_metrics(self):
        """Collect and store memory usage metrics"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            system_memory = psutil.virtual_memory()
            
            # Force garbage collection and count objects
            gc_count = len(gc.get_objects())
            gc.collect()
            
            # Convert to MB
            rss_mb = memory_info.rss / (1024 * 1024)
            vms_mb = memory_info.vms / (1024 * 1024)
            available_mb = system_memory.available / (1024 * 1024)
            memory_percent = process.memory_percent()
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO memory_usage (rss_mb, vms_mb, memory_percent, available_mb, gc_count)
                VALUES (?, ?, ?, ?, ?)
            """, (rss_mb, vms_mb, memory_percent, available_mb, gc_count))
            conn.commit()
            conn.close()
            
            # Check for memory warnings
            if memory_percent > self.MEMORY_WARNING_THRESHOLD:
                self._create_alert('memory_warning', 'high', 
                    f'High memory usage: {memory_percent:.1f}% ({rss_mb:.1f} MB)')
                    
        except Exception as e:
            logging.error(f"Error collecting memory metrics: {e}")
            
    def _check_performance_alerts(self):
        """Check for various performance issues"""
        try:
            # Check for slow queries in last 5 minutes
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM query_performance 
                WHERE execution_time > ? AND timestamp > datetime('now', '-5 minutes')
            """, (self.QUERY_WARNING_THRESHOLD,))
            
            slow_queries = cursor.fetchone()[0]
            if slow_queries > 5:
                self._create_alert('slow_queries', 'medium',
                    f'{slow_queries} slow queries detected in last 5 minutes')
            
            # Check for long-running sessions
            cursor.execute("""
                SELECT COUNT(*) FROM session_performance 
                WHERE total_duration > ? AND session_end IS NULL
            """, (self.SESSION_WARNING_THRESHOLD,))
            
            long_sessions = cursor.fetchone()[0]
            if long_sessions > 0:
                self._create_alert('long_sessions', 'medium',
                    f'{long_sessions} sessions running longer than 1 hour')
            
            conn.close()
            
        except Exception as e:
            logging.error(f"Error checking performance alerts: {e}")
            
    def _create_alert(self, alert_type: str, severity: str, message: str):
        """Create a system alert"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_alerts (alert_type, severity, message)
                VALUES (?, ?, ?)
            """, (alert_type, severity, message))
            conn.commit()
            conn.close()
            
            logging.warning(f"{alert_type.upper()}: {message}")
            
        except Exception as e:
            logging.error(f"Error creating alert: {e}")
            
    def log_query_performance(self, function_name: str, execution_time: float, 
                            parameters: Dict = None, result_size: int = None,
                            error_message: str = None):
        """Log query performance data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO query_performance 
                (function_name, execution_time, parameters, result_size, error_message)
                VALUES (?, ?, ?, ?, ?)
            """, (function_name, execution_time, 
                 json.dumps(parameters) if parameters else None,
                 result_size, error_message))
            conn.commit()
            conn.close()
            
            # Check for slow query
            if execution_time > self.QUERY_WARNING_THRESHOLD:
                logging.warning(f"Slow query: {function_name} took {execution_time:.2f}s")
                
        except Exception as e:
            logging.error(f"Error logging query performance: {e}")
            
    def log_session_performance(self, student_id: str, session_start: datetime,
                              session_end: datetime = None, phases_completed: int = 0,
                              memory_peak_mb: float = None, task_switches: int = 0,
                              warnings: List[str] = None):
        """Log session performance data"""
        try:
            total_duration = None
            if session_end and session_start:
                total_duration = (session_end - session_start).total_seconds()
                
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO session_performance 
                (student_id, session_start, session_end, total_duration, 
                 phases_completed, memory_peak_mb, task_switches, warnings)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (student_id, session_start, session_end, total_duration,
                 phases_completed, memory_peak_mb, task_switches,
                 json.dumps(warnings) if warnings else None))
            conn.commit()
            conn.close()
            
            # Check for long session
            if total_duration and total_duration > self.SESSION_WARNING_THRESHOLD:
                self._create_alert('long_session', 'low',
                    f'Student {student_id} session lasted {total_duration/3600:.1f} hours')
                    
        except Exception as e:
            logging.error(f"Error logging session performance: {e}")
            
    def get_performance_report(self, hours: int = 24) -> Dict:
        """Generate performance report for last N hours"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Memory usage stats
            cursor.execute("""
                SELECT 
                    AVG(memory_percent) as avg_memory,
                    MAX(memory_percent) as peak_memory,
                    COUNT(*) as measurements
                FROM memory_usage 
                WHERE timestamp > datetime('now', '-{} hours')
            """.format(hours))
            memory_stats = cursor.fetchone()
            
            # Query performance stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_queries,
                    AVG(execution_time) as avg_time,
                    MAX(execution_time) as max_time,
                    COUNT(CASE WHEN execution_time > ? THEN 1 END) as slow_queries
                FROM query_performance 
                WHERE timestamp > datetime('now', '-{} hours')
            """.format(hours), (self.QUERY_WARNING_THRESHOLD,))
            query_stats = cursor.fetchone()
            
            # Session stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_sessions,
                    AVG(total_duration) as avg_duration,
                    MAX(total_duration) as max_duration,
                    AVG(phases_completed) as avg_phases
                FROM session_performance 
                WHERE session_start > datetime('now', '-{} hours')
            """.format(hours))
            session_stats = cursor.fetchone()
            
            # Recent alerts
            cursor.execute("""
                SELECT alert_type, severity, message, timestamp
                FROM system_alerts 
                WHERE timestamp > datetime('now', '-{} hours')
                ORDER BY timestamp DESC
                LIMIT 10
            """.format(hours))
            recent_alerts = cursor.fetchall()
            
            conn.close()
            
            return {
                'report_period_hours': hours,
                'generated_at': datetime.now().isoformat(),
                'memory_usage': {
                    'average_percent': memory_stats[0] if memory_stats[0] else 0,
                    'peak_percent': memory_stats[1] if memory_stats[1] else 0,
                    'measurements': memory_stats[2] if memory_stats[2] else 0
                },
                'query_performance': {
                    'total_queries': query_stats[0] if query_stats[0] else 0,
                    'average_time_seconds': query_stats[1] if query_stats[1] else 0,
                    'max_time_seconds': query_stats[2] if query_stats[2] else 0,
                    'slow_queries': query_stats[3] if query_stats[3] else 0
                },
                'session_performance': {
                    'total_sessions': session_stats[0] if session_stats[0] else 0,
                    'average_duration_seconds': session_stats[1] if session_stats[1] else 0,
                    'max_duration_seconds': session_stats[2] if session_stats[2] else 0,
                    'average_phases_completed': session_stats[3] if session_stats[3] else 0
                },
                'recent_alerts': [
                    {
                        'type': alert[0],
                        'severity': alert[1], 
                        'message': alert[2],
                        'timestamp': alert[3]
                    } for alert in recent_alerts
                ]
            }
            
        except Exception as e:
            logging.error(f"Error generating performance report: {e}")
            return {}
            
    def optimize_database(self):
        """Optimize database performance"""
        optimizations_applied = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create indexes for better query performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_memory_timestamp ON memory_usage(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_query_function ON query_performance(function_name)",
                "CREATE INDEX IF NOT EXISTS idx_query_timestamp ON query_performance(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_session_student ON session_performance(student_id)",
                "CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON system_alerts(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_alerts_type ON system_alerts(alert_type)"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
                optimizations_applied.append(index_sql.split("ON")[1].strip())
                
            # Vacuum database
            cursor.execute("VACUUM")
            optimizations_applied.append("Database vacuum completed")
            
            # Analyze tables
            cursor.execute("ANALYZE")
            optimizations_applied.append("Table statistics updated")
            
            conn.commit()
            conn.close()
            
            # Clean old data (keep last 7 days)
            self.cleanup_old_data(days=7)
            optimizations_applied.append("Old data cleaned up")
            
            logging.info(f"Database optimization completed: {optimizations_applied}")
            return optimizations_applied
            
        except Exception as e:
            logging.error(f"Error optimizing database: {e}")
            return []
            
    def cleanup_old_data(self, days: int = 7):
        """Clean up old performance data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            tables = ['memory_usage', 'query_performance', 'system_alerts']
            deleted_rows = 0
            
            for table in tables:
                cursor.execute(f"""
                    DELETE FROM {table} 
                    WHERE timestamp < datetime('now', '-{days} days')
                """)
                deleted_rows += cursor.rowcount
                
            # Keep completed sessions but clean very old ones
            cursor.execute("""
                DELETE FROM session_performance 
                WHERE session_start < datetime('now', '-{} days')
                AND session_end IS NOT NULL
            """.format(days * 2))  # Keep session data longer
            deleted_rows += cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logging.info(f"Cleaned up {deleted_rows} old performance records")
            return deleted_rows
            
        except Exception as e:
            logging.error(f"Error cleaning up old data: {e}")
            return 0

def performance_test():
    """Run performance tests on the Korean Learning System"""
    monitor = PerformanceMonitor()
    
    print("🔍 Performance Testing Korean Learning System")
    print("=" * 60)
    
    # Start monitoring
    monitor.start_monitoring(interval_seconds=5)
    
    # Simulate various operations
    import requests
    import time
    
    base_url = "http://127.0.0.1:8080"
    
    print("📊 Testing system performance...")
    
    # Test 1: Memory usage baseline
    print("1. Measuring baseline memory usage...")
    time.sleep(2)
    
    # Test 2: Load multiple tasks
    print("2. Loading learning tasks...")
    start_time = time.time()
    for i in range(5):
        try:
            response = requests.get(f"{base_url}/learning/get_task", timeout=5)
            if response.status_code == 200:
                monitor.log_query_performance(
                    'get_task', 
                    time.time() - start_time, 
                    {'iteration': i}
                )
        except Exception as e:
            monitor.log_query_performance(
                'get_task', 
                time.time() - start_time, 
                {'iteration': i},
                error_message=str(e)
            )
    
    # Test 3: Teacher dashboard load
    print("3. Testing teacher dashboard performance...")
    start_time = time.time()
    try:
        response = requests.get(f"{base_url}/teacher/api/classes", timeout=5)
        monitor.log_query_performance(
            'teacher_classes',
            time.time() - start_time
        )
    except Exception as e:
        monitor.log_query_performance(
            'teacher_classes',
            time.time() - start_time,
            error_message=str(e)
        )
    
    # Wait for monitoring data
    time.sleep(10)
    
    # Stop monitoring and generate report
    monitor.stop_monitoring()
    
    print("4. Generating performance report...")
    report = monitor.get_performance_report(hours=1)
    
    print("\n📋 Performance Report")
    print("=" * 40)
    print(f"Memory Usage: {report['memory_usage']['average_percent']:.1f}% avg, {report['memory_usage']['peak_percent']:.1f}% peak")
    print(f"Query Performance: {report['query_performance']['total_queries']} queries, {report['query_performance']['average_time_seconds']:.3f}s avg")
    print(f"Slow Queries: {report['query_performance']['slow_queries']}")
    
    if report['recent_alerts']:
        print("\n⚠️ Recent Alerts:")
        for alert in report['recent_alerts']:
            print(f"  - {alert['severity'].upper()}: {alert['message']}")
    else:
        print("\n✅ No performance alerts")
    
    # Optimize database
    print("\n🔧 Optimizing database...")
    optimizations = monitor.optimize_database()
    for opt in optimizations:
        print(f"  ✅ {opt}")
    
    print("\n🎉 Performance testing completed!")
    return report

if __name__ == "__main__":
    performance_test()