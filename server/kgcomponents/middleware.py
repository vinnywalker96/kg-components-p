import re
import logging
import time
from django.conf import settings
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers to all responses.
    """
    def process_response(self, request, response):
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Add Content-Security-Policy in production
        if not settings.DEBUG:
            response['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'"
        
        return response


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all requests for security auditing.
    """
    def process_request(self, request):
        # Set request start time
        request.start_time = time.time()
        
        # Log the request
        logger.info(f"Request: {request.method} {request.path} from {request.META.get('REMOTE_ADDR')}")
        
        return None
    
    def process_response(self, request, response):
        # Calculate request duration
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            logger.info(f"Response: {response.status_code} in {duration:.2f}s")
        
        return response


class SQLInjectionProtectionMiddleware(MiddlewareMixin):
    """
    Middleware to protect against SQL injection attacks.
    """
    def process_request(self, request):
        # Check for SQL injection patterns in GET parameters
        for key, value in request.GET.items():
            if self._contains_sql_injection(value):
                logger.warning(f"Potential SQL injection detected in GET parameter: {key}={value}")
                return HttpResponseForbidden("Forbidden")
        
        # Check for SQL injection patterns in POST parameters
        if request.method == 'POST' and request.content_type == 'application/x-www-form-urlencoded':
            for key, value in request.POST.items():
                if self._contains_sql_injection(value):
                    logger.warning(f"Potential SQL injection detected in POST parameter: {key}={value}")
                    return HttpResponseForbidden("Forbidden")
        
        return None
    
    def _contains_sql_injection(self, value):
        """
        Check if a value contains SQL injection patterns.
        """
        if not isinstance(value, str):
            return False
        
        # Common SQL injection patterns
        patterns = [
            r'(\s|^)(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|EXEC|UNION|CREATE|WHERE)(\s|$)',
            r'(\s|^)(OR|AND)(\s+)(\d+|\'[^\']*\'|\"[^\"]*\")(\s*)(=|<|>|<=|>=)(\s*)(\d+|\'[^\']*\'|\"[^\"]*\")',
            r'--',
            r'\/\*.*\*\/',
            r';.*',
            r'(\s|^)(SLEEP|BENCHMARK|WAITFOR|DELAY)(\s*)\(',
        ]
        
        for pattern in patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        
        return False

