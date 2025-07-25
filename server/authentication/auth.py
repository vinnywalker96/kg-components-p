from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)

class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication class that extends the default JWTAuthentication
    to add additional security checks and better error handling.
    """
    
    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        try:
            # Call the parent authenticate method
            result = super().authenticate(request)
            
            if result is None:
                return None
            
            user, token = result
            
            # Additional security checks
            if not user.is_active:
                logger.warning(f"Authentication attempt with inactive user: {user.email}")
                raise AuthenticationFailed(_('User account is disabled.'))
                
            # For endpoints that require email verification
            if getattr(request.resolver_match.func.view_class, 'requires_verification', False):
                if not user.is_verified:
                    logger.warning(f"Unverified user attempting to access protected endpoint: {user.email}")
                    raise AuthenticationFailed(_('Email verification required.'))
            
            return user, token
            
        except InvalidToken as e:
            logger.warning(f"Invalid token: {str(e)}")
            raise AuthenticationFailed(_('Invalid token.'))
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise AuthenticationFailed(_('Authentication failed.'))
            
    def get_user(self, validated_token):
        """
        Attempt to find and return a user using the given validated token.
        """
        try:
            user = super().get_user(validated_token)
            
            # Additional security check
            if user is None:
                logger.warning(f"No user found for token: {validated_token}")
                raise AuthenticationFailed(_('No user found for the given token.'))
                
            return user
            
        except Exception as e:
            logger.error(f"Error getting user from token: {str(e)}")
            raise AuthenticationFailed(_('Invalid token.'))

