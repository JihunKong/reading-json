#!/usr/bin/env python3
"""
Security and Error Handling Improvements for Korean Learning System
"""

import re
import html
import json
from functools import wraps
from flask import request, jsonify
from typing import Any, Dict, List, Optional, Union
import logging

# Set up logging for security events
security_logger = logging.getLogger('security')
handler = logging.FileHandler('security.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
security_logger.addHandler(handler)
security_logger.setLevel(logging.WARNING)

class SecurityValidator:
    """Security validation utilities"""
    
    # XSS prevention patterns
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
        r'<link[^>]*>',
        r'<meta[^>]*>',
        r'<style[^>]*>.*?</style>',
        r'expression\s*\(',
        r'vbscript:',
        r'data:\s*text/html'
    ]
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)',
        r'(--|#|/\*|\*/)',
        r'(\bOR\b.*=.*\bOR\b)',
        r'(\bAND\b.*=.*\bAND\b)',
        r'(\'\s*(OR|AND)\s*\'\w*\'\s*=\s*\'\w*)',
        r'(\d+\s*(=|<|>)\s*\d+)'
    ]
    
    @staticmethod
    def sanitize_input(data: Any) -> Any:
        """Sanitize input data to prevent XSS and injection attacks"""
        if isinstance(data, str):
            return SecurityValidator._sanitize_string(data)
        elif isinstance(data, dict):
            return {k: SecurityValidator.sanitize_input(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [SecurityValidator.sanitize_input(item) for item in data]
        else:
            return data
    
    @staticmethod
    def _sanitize_string(text: str) -> str:
        """Sanitize a string input"""
        if not text:
            return text
            
        # HTML escape
        text = html.escape(text)
        
        # Remove potentially dangerous patterns
        for pattern in SecurityValidator.XSS_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Limit length to prevent DoS
        if len(text) > 10000:
            text = text[:10000]
            
        return text
    
    @staticmethod
    def validate_korean_text(text: str) -> bool:
        """Validate Korean text input"""
        if not text:
            return True
            
        # Check for basic Korean characters
        korean_pattern = r'[가-힣\s\d.,!?;:()\-"\']+$'
        
        # Allow some English characters for mixed content
        mixed_pattern = r'[가-힣a-zA-Z\s\d.,!?;:()\-"\']+$'
        
        return bool(re.match(mixed_pattern, text))
    
    @staticmethod
    def detect_sql_injection(text: str) -> bool:
        """Detect potential SQL injection attempts"""
        if not text:
            return False
            
        for pattern in SecurityValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

class ErrorHandler:
    """Enhanced error handling utilities"""
    
    ERROR_MESSAGES_KO = {
        'invalid_input': '잘못된 입력입니다. 다시 시도해주세요.',
        'session_expired': '세션이 만료되었습니다. 다시 로그인해주세요.',
        'task_not_found': '학습 과제를 찾을 수 없습니다.',
        'phase_error': '학습 단계 처리 중 오류가 발생했습니다.',
        'network_error': '네트워크 오류가 발생했습니다. 연결을 확인해주세요.',
        'server_error': '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
        'permission_denied': '접근 권한이 없습니다.',
        'rate_limit': '너무 많은 요청을 보내셨습니다. 잠시 후 다시 시도해주세요.',
        'validation_error': '입력 데이터가 올바르지 않습니다.',
        'korean_text_required': '한국어 텍스트만 입력 가능합니다.',
        'unsafe_content': '안전하지 않은 내용이 감지되었습니다.'
    }
    
    @staticmethod
    def create_error_response(error_type: str, details: str = None, status_code: int = 400) -> tuple:
        """Create standardized error response"""
        message = ErrorHandler.ERROR_MESSAGES_KO.get(error_type, '알 수 없는 오류가 발생했습니다.')
        
        response_data = {
            'success': False,
            'error_type': error_type,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        if details and isinstance(details, str) and len(details) < 200:
            response_data['details'] = details
        
        # Log security events
        if error_type in ['unsafe_content', 'permission_denied', 'rate_limit']:
            security_logger.warning(f"Security event: {error_type} - {details}")
        
        return jsonify(response_data), status_code
    
    @staticmethod
    def handle_exception(func):
        """Decorator to handle exceptions with Korean error messages"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValueError as e:
                return ErrorHandler.create_error_response('validation_error', str(e), 400)
            except PermissionError as e:
                return ErrorHandler.create_error_response('permission_denied', str(e), 403)
            except FileNotFoundError as e:
                return ErrorHandler.create_error_response('task_not_found', str(e), 404)
            except Exception as e:
                # Log the full exception for debugging
                logging.error(f"Unhandled exception in {func.__name__}: {str(e)}", exc_info=True)
                return ErrorHandler.create_error_response('server_error', None, 500)
        return wrapper

class InputValidator:
    """Input validation utilities with Korean language support"""
    
    @staticmethod
    def validate_student_response(data: Dict) -> tuple[bool, str]:
        """Validate student response data"""
        if not isinstance(data, dict):
            return False, "응답 데이터가 올바른 형식이 아닙니다."
        
        # Check for required fields based on context
        response_data = data.get('response_data', {})
        
        # Validate response data structure
        if not isinstance(response_data, dict):
            return False, "응답 데이터 구조가 올바르지 않습니다."
        
        # Check for XSS and injection attempts
        for key, value in response_data.items():
            if isinstance(value, str):
                if SecurityValidator.detect_sql_injection(value):
                    return False, "안전하지 않은 내용이 감지되었습니다."
                
                # Validate Korean text for text responses
                if key in ['text_response', 'summary', 'answer']:
                    if not SecurityValidator.validate_korean_text(value):
                        return False, "한국어 텍스트만 입력 가능합니다."
        
        return True, ""
    
    @staticmethod
    def validate_teacher_intervention(data: Dict) -> tuple[bool, str]:
        """Validate teacher intervention data"""
        if not isinstance(data, dict):
            return False, "개입 데이터가 올바른 형식이 아닙니다."
        
        intervention_type = data.get('type', '')
        message = data.get('message', '')
        
        # Validate intervention type
        valid_types = ['hint', 'skip', 'reset', 'help_message']
        if intervention_type not in valid_types:
            return False, "올바르지 않은 개입 유형입니다."
        
        # Validate message
        if message and isinstance(message, str):
            if len(message) > 500:
                return False, "메시지가 너무 깁니다. 500자 이내로 입력해주세요."
            
            if not SecurityValidator.validate_korean_text(message):
                return False, "한국어 메시지만 입력 가능합니다."
            
            if SecurityValidator.detect_sql_injection(message):
                return False, "안전하지 않은 내용이 감지되었습니다."
        
        return True, ""
    
    @staticmethod
    def validate_class_data(data: Dict) -> tuple[bool, str]:
        """Validate class-related data"""
        if not isinstance(data, dict):
            return False, "학급 데이터가 올바른 형식이 아닙니다."
        
        # Validate student name
        if 'student_name' in data:
            name = data['student_name']
            if not name or len(name) > 50:
                return False, "학생 이름은 1-50자 사이여야 합니다."
            
            if not SecurityValidator.validate_korean_text(name):
                return False, "한국어 이름만 입력 가능합니다."
        
        # Validate class ID format
        if 'class_id' in data:
            class_id = data['class_id']
            if not re.match(r'^[a-zA-Z0-9_-]{1,50}$', class_id):
                return False, "올바르지 않은 학급 ID 형식입니다."
        
        return True, ""

# Rate limiting storage (in production, use Redis)
rate_limit_storage = {}

def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """Simple rate limiting decorator"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from datetime import datetime, timedelta
            
            # Get client IP
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
            
            current_time = datetime.now()
            
            # Clean old entries
            if client_ip in rate_limit_storage:
                rate_limit_storage[client_ip] = [
                    timestamp for timestamp in rate_limit_storage[client_ip]
                    if current_time - timestamp < timedelta(seconds=window_seconds)
                ]
            else:
                rate_limit_storage[client_ip] = []
            
            # Check rate limit
            if len(rate_limit_storage[client_ip]) >= max_requests:
                return ErrorHandler.create_error_response('rate_limit', None, 429)
            
            # Add current request
            rate_limit_storage[client_ip].append(current_time)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def secure_json_response(data: Any) -> str:
    """Create secure JSON response"""
    # Sanitize the data
    sanitized_data = SecurityValidator.sanitize_input(data)
    
    # Use secure JSON encoding
    return json.dumps(sanitized_data, ensure_ascii=False, separators=(',', ':'))

def validate_and_sanitize_request():
    """Middleware to validate and sanitize all requests"""
    # Skip validation for static files
    if request.path.startswith('/static'):
        return
    
    # Validate content type for POST requests
    if request.method == 'POST':
        if not request.is_json and 'application/json' not in request.content_type:
            return ErrorHandler.create_error_response('invalid_input', 'JSON content type required', 400)
    
    # Sanitize request data
    if request.is_json:
        try:
            request._cached_json = SecurityValidator.sanitize_input(request.get_json())
        except Exception:
            return ErrorHandler.create_error_response('invalid_input', 'Invalid JSON format', 400)

# Enhanced security headers
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdn.socket.io; style-src 'self' 'unsafe-inline'"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

# Performance monitoring
class PerformanceMonitor:
    """Monitor performance and detect potential issues"""
    
    @staticmethod
    def monitor_memory_usage():
        """Monitor memory usage and detect leaks"""
        import psutil
        import gc
        
        # Get current memory usage
        process = psutil.Process()
        memory_info = process.memory_info()
        
        # Force garbage collection
        gc.collect()
        
        return {
            'rss': memory_info.rss,
            'vms': memory_info.vms,
            'percent': process.memory_percent(),
            'available': psutil.virtual_memory().available
        }
    
    @staticmethod
    def log_slow_query(func_name: str, execution_time: float, threshold: float = 1.0):
        """Log slow operations"""
        if execution_time > threshold:
            logging.warning(f"Slow operation detected: {func_name} took {execution_time:.2f}s")

if __name__ == "__main__":
    # Test security validator
    test_inputs = [
        "<script>alert('xss')</script>",
        "'; DROP TABLE users; --",
        "안녕하세요. 이것은 정상적인 한국어 입력입니다.",
        "javascript:alert('test')",
        "1' OR '1'='1"
    ]
    
    for test_input in test_inputs:
        sanitized = SecurityValidator.sanitize_input(test_input)
        is_korean = SecurityValidator.validate_korean_text(test_input)
        has_sql_injection = SecurityValidator.detect_sql_injection(test_input)
        
        print(f"Input: {test_input}")
        print(f"Sanitized: {sanitized}")
        print(f"Is Korean: {is_korean}")
        print(f"Has SQL injection: {has_sql_injection}")
        print("-" * 50)