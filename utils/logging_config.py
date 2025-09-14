"""
Production Logging Configuration for Korean Reading Comprehension System
Provides structured logging with multiple formats and destinations
"""

import os
import sys
import json
import logging
import logging.handlers
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import traceback
from pythonjsonlogger import jsonlogger
from config.config import get_config

# Custom JSON formatter for structured logging
class StructuredJSONFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional context"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super(StructuredJSONFormatter, self).add_fields(log_record, record, message_dict)
        
        # Add timestamp
        if not log_record.get('timestamp'):
            log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Add service information
        log_record['service'] = 'korean-reading-system'
        log_record['environment'] = os.getenv('ENVIRONMENT', 'development')
        log_record['version'] = os.getenv('APP_VERSION', '1.0.0')
        
        # Add container information if available
        hostname = os.getenv('HOSTNAME')
        if hostname:
            log_record['container_id'] = hostname
        
        # Add level name
        if log_record.get('levelname'):
            log_record['level'] = log_record['levelname'].lower()
        
        # Add trace information for errors
        if record.exc_info:
            log_record['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }


class KoreanReadingSystemLogger:
    """Main logger class for the Korean Reading System"""
    
    def __init__(self):
        self.config = get_config()
        self.loggers: Dict[str, logging.Logger] = {}
        self._setup_root_logger()
    
    def _setup_root_logger(self):
        """Setup root logger configuration"""
        # Clear any existing handlers
        logging.getLogger().handlers.clear()
        
        # Set root level
        logging.getLogger().setLevel(getattr(logging, self.config.logging.level.upper()))
        
        # Disable propagation for third-party loggers to reduce noise
        self._configure_third_party_loggers()
    
    def _configure_third_party_loggers(self):
        """Configure third-party library loggers"""
        # Set appropriate levels for noisy libraries
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
        logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
        logging.getLogger('celery').setLevel(logging.INFO)
        logging.getLogger('pika').setLevel(logging.WARNING)
        logging.getLogger('redis').setLevel(logging.WARNING)
    
    def get_logger(self, name: str, context: Optional[Dict[str, Any]] = None) -> logging.Logger:
        """Get a configured logger for a specific component"""
        if name in self.loggers:
            return self.loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, self.config.logging.level.upper()))
        
        # Clear existing handlers
        logger.handlers.clear()
        logger.propagate = False
        
        # Add handlers
        self._add_console_handler(logger)
        self._add_file_handler(logger)
        
        if self.config.logging.syslog_enabled:
            self._add_syslog_handler(logger)
        
        # Add context filter if provided
        if context:
            logger.addFilter(ContextFilter(context))
        
        self.loggers[name] = logger
        return logger
    
    def _add_console_handler(self, logger: logging.Logger):
        """Add console handler with appropriate formatter"""
        console_handler = logging.StreamHandler(sys.stdout)
        
        if self.config.logging.format.lower() == 'json':
            formatter = StructuredJSONFormatter()
        else:
            formatter = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    def _add_file_handler(self, logger: logging.Logger):
        """Add rotating file handler"""
        log_dir = Path(self.config.logging.file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Parse max size (e.g., "100MB" -> 100 * 1024 * 1024)
        max_size = self._parse_size(self.config.logging.max_size)
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename=self.config.logging.file_path,
            maxBytes=max_size,
            backupCount=self.config.logging.backup_count,
            encoding='utf-8'
        )
        
        if self.config.logging.format.lower() == 'json':
            formatter = StructuredJSONFormatter()
        else:
            formatter = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    def _add_syslog_handler(self, logger: logging.Logger):
        """Add syslog handler for centralized logging"""
        try:
            syslog_handler = logging.handlers.SysLogHandler(
                address=(self.config.logging.syslog_host, self.config.logging.syslog_port)
            )
            
            formatter = logging.Formatter(
                fmt='korean-reading-system: %(name)s - %(levelname)s - %(message)s'
            )
            
            syslog_handler.setFormatter(formatter)
            logger.addHandler(syslog_handler)
            
        except Exception as e:
            print(f"Failed to setup syslog handler: {e}")
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string like '100MB' to bytes"""
        size_str = size_str.upper().strip()
        
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)


class ContextFilter(logging.Filter):
    """Filter to add context information to log records"""
    
    def __init__(self, context: Dict[str, Any]):
        super().__init__()
        self.context = context
    
    def filter(self, record: logging.LogRecord) -> bool:
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


class RequestContextLogger:
    """Logger with request context for web applications"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def info(self, message: str, **kwargs):
        """Log info with request context"""
        extra = self._get_request_context()
        extra.update(kwargs)
        self.logger.info(message, extra=extra)
    
    def warning(self, message: str, **kwargs):
        """Log warning with request context"""
        extra = self._get_request_context()
        extra.update(kwargs)
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, **kwargs):
        """Log error with request context"""
        extra = self._get_request_context()
        extra.update(kwargs)
        self.logger.error(message, extra=extra)
    
    def exception(self, message: str, **kwargs):
        """Log exception with request context"""
        extra = self._get_request_context()
        extra.update(kwargs)
        self.logger.exception(message, extra=extra)
    
    def _get_request_context(self) -> Dict[str, Any]:
        """Get current request context"""
        context = {}
        
        try:
            # Try to get Flask request context
            from flask import request, g
            if request:
                context.update({
                    'method': request.method,
                    'path': request.path,
                    'remote_addr': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', ''),
                })
                
                # Add user context if available
                if hasattr(g, 'user_id'):
                    context['user_id'] = g.user_id
                if hasattr(g, 'session_id'):
                    context['session_id'] = g.session_id
                    
        except ImportError:
            pass
        except RuntimeError:
            # Outside request context
            pass
        
        return context


class PerformanceLogger:
    """Logger for performance monitoring"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_timing(self, operation: str, duration: float, **kwargs):
        """Log operation timing"""
        extra = {
            'operation': operation,
            'duration_ms': round(duration * 1000, 2),
            'metric_type': 'timing'
        }
        extra.update(kwargs)
        
        if duration > 1.0:  # Log slow operations as warnings
            self.logger.warning(f"Slow operation: {operation}", extra=extra)
        else:
            self.logger.info(f"Operation completed: {operation}", extra=extra)
    
    def log_counter(self, metric: str, value: int = 1, **kwargs):
        """Log counter metrics"""
        extra = {
            'metric': metric,
            'value': value,
            'metric_type': 'counter'
        }
        extra.update(kwargs)
        
        self.logger.info(f"Counter: {metric}", extra=extra)
    
    def log_gauge(self, metric: str, value: float, **kwargs):
        """Log gauge metrics"""
        extra = {
            'metric': metric,
            'value': value,
            'metric_type': 'gauge'
        }
        extra.update(kwargs)
        
        self.logger.info(f"Gauge: {metric}", extra=extra)


class SecurityLogger:
    """Logger for security events"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_authentication(self, user_id: str, success: bool, **kwargs):
        """Log authentication attempts"""
        extra = {
            'user_id': user_id,
            'success': success,
            'event_type': 'authentication'
        }
        extra.update(kwargs)
        
        if success:
            self.logger.info("User authentication successful", extra=extra)
        else:
            self.logger.warning("User authentication failed", extra=extra)
    
    def log_authorization(self, user_id: str, resource: str, action: str, success: bool, **kwargs):
        """Log authorization attempts"""
        extra = {
            'user_id': user_id,
            'resource': resource,
            'action': action,
            'success': success,
            'event_type': 'authorization'
        }
        extra.update(kwargs)
        
        if success:
            self.logger.info("Authorization granted", extra=extra)
        else:
            self.logger.warning("Authorization denied", extra=extra)
    
    def log_suspicious_activity(self, description: str, **kwargs):
        """Log suspicious activities"""
        extra = {
            'description': description,
            'event_type': 'suspicious_activity'
        }
        extra.update(kwargs)
        
        self.logger.error("Suspicious activity detected", extra=extra)


# Global logger manager
_logger_manager = None

def get_logger_manager() -> KoreanReadingSystemLogger:
    """Get global logger manager"""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = KoreanReadingSystemLogger()
    return _logger_manager


def get_logger(name: str, context: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """Get configured logger - convenience function"""
    return get_logger_manager().get_logger(name, context)


def get_request_logger(name: str) -> RequestContextLogger:
    """Get request context logger"""
    logger = get_logger(name)
    return RequestContextLogger(logger)


def get_performance_logger(name: str) -> PerformanceLogger:
    """Get performance logger"""
    logger = get_logger(name)
    return PerformanceLogger(logger)


def get_security_logger(name: str) -> SecurityLogger:
    """Get security logger"""
    logger = get_logger(name)
    return SecurityLogger(logger)


# Context manager for timing operations
class timer:
    """Context manager for timing operations"""
    
    def __init__(self, operation: str, logger: Optional[PerformanceLogger] = None):
        self.operation = operation
        self.logger = logger or get_performance_logger('timer')
        self.start_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        if self.start_time:
            duration = time.time() - self.start_time
            self.logger.log_timing(self.operation, duration)


if __name__ == "__main__":
    # Test logging configuration
    logger = get_logger('test')
    request_logger = get_request_logger('test.request')
    perf_logger = get_performance_logger('test.performance')
    security_logger = get_security_logger('test.security')
    
    # Test different log levels
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    # Test performance logging
    with timer('test_operation', perf_logger):
        import time
        time.sleep(0.1)
    
    # Test security logging
    security_logger.log_authentication('user123', True)
    security_logger.log_authorization('user123', 'questions', 'read', True)
    
    print("Logging test completed")