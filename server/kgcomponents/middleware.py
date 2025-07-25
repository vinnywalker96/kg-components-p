import re
import time
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden, JsonResponse
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all responses.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; connect-src 'self'"
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response


class RateLimitMiddleware:
    """
    Middleware to implement rate limiting.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limits = {}
        self.window_size = getattr(settings, 'RATE_LIMIT_WINDOW', 60)  # 60 seconds
        self.max_requests = getattr(settings, 'RATE_LIMIT_MAX_REQUESTS', 100)  # 100 requests per window
        
    def __call__(self, request):
        # Skip rate limiting for certain paths
        if self._should_skip_rate_limiting(request):
            return self.get_response(request)
            
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check if client is rate limited
        current_time = time.time()
        if client_ip in self.rate_limits:
            requests, window_start = self.rate_limits[client_ip]
            
            # Reset window if it has expired
            if current_time - window_start > self.window_size:
                self.rate_limits[client_ip] = (1, current_time)
            else:
                # Increment request count
                requests += 1
                self.rate_limits[client_ip] = (requests, window_start)
                
                # Check if rate limit exceeded
                if requests > self.max_requests:
                    return JsonResponse({
                        'error': 'Rate limit exceeded. Please try again later.'
                    }, status=429)
        else:
            # First request from this client
            self.rate_limits[client_ip] = (1, current_time)
            
        return self.get_response(request)
        
    def _get_client_ip(self, request):
        """
        Get the client IP address from the request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
        
    def _should_skip_rate_limiting(self, request):
        """
        Check if rate limiting should be skipped for this request.
        """
        # Skip rate limiting for admin paths
        if request.path.startswith('/admin/'):
            return True
            
        # Skip rate limiting for static files
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return True
            
        return False


class RequestLoggingMiddleware:
    """
    Middleware to log all requests for security auditing.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Log request details
        client_ip = self._get_client_ip(request)
        method = request.method
        path = request.path
        user = request.user.email if request.user.is_authenticated else 'Anonymous'
        
        logger.info(f"Request: {method} {path} - IP: {client_ip} - User: {user}")
        
        # Process request
        response = self.get_response(request)
        
        # Log response status
        logger.info(f"Response: {method} {path} - Status: {response.status_code}")
        
        return response
        
    def _get_client_ip(self, request):
        """
        Get the client IP address from the request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SQLInjectionProtectionMiddleware:
    """
    Middleware to protect against SQL injection attacks.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.sql_patterns = [
            r'(\s|^)(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE)(\s|$)',
            r'(\s|^)(UNION|JOIN|OR|AND)(\s|$)',
            r'--',
            r';',
            r'\/\*.*\*\/',
        ]
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.sql_patterns]
        
    def __call__(self, request):
        # Check for SQL injection patterns in query parameters
        for key, value in request.GET.items():
            if self._contains_sql_injection(value):
                logger.warning(f"Potential SQL injection detected in query parameter: {key}={value}")
                return HttpResponseForbidden("Forbidden")
                
        # Check for SQL injection patterns in POST data
        if request.method == 'POST':
            for key, value in request.POST.items():
                if isinstance(value, str) and self._contains_sql_injection(value):
                    logger.warning(f"Potential SQL injection detected in POST data: {key}={value}")
                    return HttpResponseForbidden("Forbidden")
                    
        return self.get_response(request)
        
    def _contains_sql_injection(self, value):
        """
        Check if a value contains SQL injection patterns.
        """
        if not isinstance(value, str):
            return False
            
        for pattern in self.compiled_patterns:
            if pattern.search(value):
                return True
                
        return False

