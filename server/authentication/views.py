from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.throttling import UserRateThrottle
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
import uuid
import logging

from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    AdminLoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    EmailVerificationSerializer,
    UserProfileSerializer
)

User = get_user_model()
logger = logging.getLogger(__name__)

class LoginRateThrottle(UserRateThrottle):
    rate = '5/min'
    scope = 'login'

class RegistrationRateThrottle(UserRateThrottle):
    rate = '3/hour'
    scope = 'registration'

class PasswordResetRateThrottle(UserRateThrottle):
    rate = '3/hour'
    scope = 'password_reset'

class UserRegistrationView(generics.CreateAPIView):
    """
    API view for user registration.
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    throttle_classes = [RegistrationRateThrottle]
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate verification token
            token = str(uuid.uuid4())
            user.verification_token = token
            user.verification_token_created_at = timezone.now()
            user.save()
            
            # Send verification email
            # TODO: Implement email sending logic
            
            return Response({
                'message': _('User registered successfully. Please check your email to verify your account.'),
                'user_id': user.id
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(TokenObtainPairView):
    """
    API view for user login.
    """
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

class AdminLoginView(TokenObtainPairView):
    """
    API view for admin login.
    """
    serializer_class = AdminLoginSerializer
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

class CustomTokenRefreshView(TokenRefreshView):
    """
    Custom token refresh view with additional security checks.
    """
    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except Exception as e:
            logger.warning(f"Token refresh failed: {str(e)}")
            return Response({
                'error': _('Invalid token or token has expired.')
            }, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(generics.GenericAPIView):
    """
    API view for user logout.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({
                    'error': _('Refresh token is required.')
                }, status=status.HTTP_400_BAD_REQUEST)
                
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({
                'message': _('Logout successful.')
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response({
                'error': _('Invalid token.')
            }, status=status.HTTP_400_BAD_REQUEST)

class EmailVerificationView(generics.GenericAPIView):
    """
    API view for email verification.
    """
    serializer_class = EmailVerificationSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            
            try:
                user = User.objects.get(verification_token=token)
                
                # Check if token is expired (24 hours)
                token_age = timezone.now() - user.verification_token_created_at
                if token_age.total_seconds() > 86400:  # 24 hours in seconds
                    return Response({
                        'error': _('Verification token has expired. Please request a new one.')
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                user.is_verified = True
                user.is_active = True
                user.verification_token = None
                user.verification_token_created_at = None
                user.save()
                
                return Response({
                    'message': _('Email verified successfully. You can now log in.')
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                return Response({
                    'error': _('Invalid verification token.')
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetRequestView(generics.GenericAPIView):
    """
    API view for password reset request.
    """
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetRateThrottle]
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email)
                
                # Generate reset token
                token = str(uuid.uuid4())
                user.reset_password_token = token
                user.reset_password_token_created_at = timezone.now()
                user.save()
                
                # Send password reset email
                # TODO: Implement email sending logic
                
                return Response({
                    'message': _('Password reset link sent to your email.')
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                # Return success even if user doesn't exist for security reasons
                return Response({
                    'message': _('Password reset link sent to your email.')
                }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmView(generics.GenericAPIView):
    """
    API view for password reset confirmation.
    """
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            password = serializer.validated_data['password']
            
            try:
                user = User.objects.get(reset_password_token=token)
                
                # Check if token is expired (1 hour)
                token_age = timezone.now() - user.reset_password_token_created_at
                if token_age.total_seconds() > 3600:  # 1 hour in seconds
                    return Response({
                        'error': _('Password reset token has expired. Please request a new one.')
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                user.set_password(password)
                user.reset_password_token = None
                user.reset_password_token_created_at = None
                user.save()
                
                return Response({
                    'message': _('Password reset successful. You can now log in with your new password.')
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                return Response({
                    'error': _('Invalid password reset token.')
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API view for retrieving and updating user profile.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user

