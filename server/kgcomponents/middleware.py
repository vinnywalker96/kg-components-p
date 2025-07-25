import re
import logging
from django.http import HttpResponseBadRequest
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to responses.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Add Content Security Policy in production
        if not request.META.get('HTTP_HOST', '').startswith(('localhost', '127.0.0.1')):
            response['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'"
        
        return response

class RequestLoggingMiddleware:
    """
    Middleware to log requests.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log request
        logger.info(f"Request: {request.method} {request.path} from {request.META.get('REMOTE_ADDR')}")
        
        response = self.get_response(request)
        
        # Log response
        logger.info(f"Response: {response.status_code} for {request.method} {request.path}")
        
        return response

class SQLInjectionProtectionMiddleware(MiddlewareMixin):
    """
    Middleware to protect against SQL injection attacks.
    """
    def process_request(self, request):
        # Check for SQL injection patterns in GET parameters
        for key, value in request.GET.items():
            if isinstance(value, str) and self._contains_sql_injection(value):
                logger.warning(f"Potential SQL injection detected in GET parameter: {key}={value}")
                return HttpResponseBadRequest("Invalid request")
        
        # Check for SQL injection patterns in POST parameters
        for key, value in request.POST.items():
            if isinstance(value, str) and self._contains_sql_injection(value):
                logger.warning(f"Potential SQL injection detected in POST parameter: {key}={value}")
                return HttpResponseBadRequest("Invalid request")
        
        return None
    
    def _contains_sql_injection(self, value):
        """
        Check if a string contains SQL injection patterns.
        """
        # List of SQL injection patterns
        sql_patterns = [
            r'(\s|^)(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE)(\s|$)',
            r'(\s|^)(UNION|JOIN|AND|OR)(\s|$)',
            r'--',
            r';(\s|$)',
            r'\/\*.*\*\/',
            r'1=1',
            r'1\s*=\s*1',
            r"'(\s|$)",
            r'"(\s|$)',
        ]
        
        # Check each pattern
        for pattern in sql_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        
        return False

