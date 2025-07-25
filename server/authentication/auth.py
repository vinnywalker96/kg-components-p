from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from django.utils.translation import gettext_lazy as _
from rest_framework import HTTP_HEADER_ENCODING
import jwt
from django.conf import settings

class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication class that extends the default SimpleJWT authentication.
    
    This class adds additional security checks and customizes the JWT authentication
    process for our application.
    """
    
    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        
        # Additional security checks can be added here
        # For example, checking if the token has been blacklisted
        
        return self.get_user(validated_token), validated_token
    
    def get_header(self, request):
        """
        Extract the header containing the JWT from the given request.
        """
        header = request.META.get('HTTP_AUTHORIZATION')
        
        if isinstance(header, str):
            # Work around django test client oddness
            header = header.encode(HTTP_HEADER_ENCODING)
            
        return header
    
    def get_raw_token(self, header):
        """
        Extract the raw JWT from the authorization header.
        """
        parts = header.split()
        
        if len(parts) == 0:
            # Empty header
            return None
            
        if len(parts) != 2:
            raise AuthenticationFailed(
                _('Authorization header must contain two space-delimited values'),
                code='bad_authorization_header',
            )
            
        if parts[0] != b'Bearer':
            raise AuthenticationFailed(
                _('Authentication credentials were not provided or are invalid.'),
                code='invalid_token_prefix',
            )
            
        return parts[1]
    
    def get_validated_token(self, raw_token):
        """
        Validate the given token and return its payload.
        """
        try:
            return super().get_validated_token(raw_token)
        except InvalidToken as e:
            raise AuthenticationFailed(
                _('Token is invalid or expired'),
                code='invalid_token',
            )


class AdminJWTAuthentication(CustomJWTAuthentication):
    """
    JWT authentication specifically for admin users.
    
    This class extends the CustomJWTAuthentication and adds additional
    checks to ensure the user is an admin.
    """
    
    def get_user(self, validated_token):
        """
        Get the user from the validated token and verify they are an admin.
        """
        user = super().get_user(validated_token)
        
        # Check if the user is an admin
        if not user.is_staff:
            raise AuthenticationFailed(
                _('User is not authorized to access admin resources'),
                code='not_admin',
            )
            
        return user

