from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
import jwt
import datetime
import secrets
import string

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import (
    UserRegistrationSerializer,
    AdminRegistrationSerializer,
    CustomTokenObtainPairSerializer,
    AdminTokenObtainPairSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    EmailVerificationSerializer
)
from .throttling import (
    LoginRateThrottle,
    RegistrationRateThrottle,
    PasswordResetRateThrottle
)

User = get_user_model()

class UserRegistrationView(APIView):
    """
    API endpoint for user registration.
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [RegistrationRateThrottle]
    
    @swagger_auto_schema(
        request_body=UserRegistrationSerializer,
        responses={
            201: openapi.Response(
                description="User registered successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'user_id': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: "Invalid input"
        }
    )
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate verification token
        token = self._generate_verification_token(user)
        
        # Send verification email (implementation depends on your email service)
        # self._send_verification_email(user, token)
        
        return Response({
            'message': _('User registered successfully. Please check your email to verify your account.'),
            'user_id': str(user.id)
        }, status=status.HTTP_201_CREATED)
    
    def _generate_verification_token(self, user):
        """
        Generate a verification token for the user.
        """
        # Generate a random token
        alphabet = string.ascii_letters + string.digits
        token = ''.join(secrets.choice(alphabet) for _ in range(64))
        
        # Store the token in the user's profile or a separate model
        # For simplicity, we'll just return it here
        return token
    
    def _send_verification_email(self, user, token):
        """
        Send a verification email to the user.
        """
        # Implementation depends on your email service
        pass


class UserLoginView(TokenObtainPairView):
    """
    API endpoint for user login.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginRateThrottle]


class AdminLoginView(TokenObtainPairView):
    """
    API endpoint for admin login.
    """
    serializer_class = AdminTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginRateThrottle]


class LogoutView(APIView):
    """
    API endpoint for user logout.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['refresh']
        ),
        responses={
            200: openapi.Response(
                description="Logged out successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: "Invalid input"
        }
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({
                'message': _('Logged out successfully')
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """
    API endpoint for requesting a password reset.
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordResetRateThrottle]
    
    @swagger_auto_schema(
        request_body=PasswordResetRequestSerializer,
        responses={
            200: openapi.Response(
                description="Password reset email sent",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: "Invalid input"
        }
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.filter(email=email).first()
        
        if user:
            # Generate reset token
            token = self._generate_reset_token(user)
            
            # Send reset email (implementation depends on your email service)
            # self._send_reset_email(user, token)
        
        # Always return success to prevent email enumeration
        return Response({
            'message': _('If an account with this email exists, a password reset link has been sent.')
        }, status=status.HTTP_200_OK)
    
    def _generate_reset_token(self, user):
        """
        Generate a password reset token for the user.
        """
        # Generate a JWT token with a short expiration
        payload = {
            'user_id': str(user.id),
            'exp': datetime.datetime.now(tz=timezone.utc) + datetime.timedelta(hours=1),
            'iat': datetime.datetime.now(tz=timezone.utc),
            'type': 'password_reset'
        }
        
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        return token
    
    def _send_reset_email(self, user, token):
        """
        Send a password reset email to the user.
        """
        # Implementation depends on your email service
        pass


class PasswordResetConfirmView(APIView):
    """
    API endpoint for confirming a password reset.
    """
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        request_body=PasswordResetConfirmSerializer,
        responses={
            200: openapi.Response(
                description="Password reset successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: "Invalid input",
            401: "Invalid or expired token"
        }
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        password = serializer.validated_data['password']
        
        try:
            # Verify the token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            
            # Check if it's a password reset token
            if payload.get('type') != 'password_reset':
                raise jwt.InvalidTokenError('Invalid token type')
            
            # Get the user
            user_id = payload.get('user_id')
            user = User.objects.get(id=user_id)
            
            # Set the new password
            user.set_password(password)
            user.save()
            
            # Blacklist all refresh tokens for the user
            tokens = OutstandingToken.objects.filter(user_id=user.id)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)
            
            return Response({
                'message': _('Password reset successful. You can now log in with your new password.')
            }, status=status.HTTP_200_OK)
            
        except (jwt.ExpiredSignatureError, jwt.DecodeError, jwt.InvalidTokenError, User.DoesNotExist) as e:
            return Response({
                'error': _('Invalid or expired token')
            }, status=status.HTTP_401_UNAUTHORIZED)


class EmailVerificationView(APIView):
    """
    API endpoint for email verification.
    """
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        request_body=EmailVerificationSerializer,
        responses={
            200: openapi.Response(
                description="Email verified successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: "Invalid input",
            401: "Invalid or expired token"
        }
    )
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        
        # Verify the token (implementation depends on your token storage)
        user = self._verify_token(token)
        
        if user:
            # Activate the user
            user.is_active = True
            user.is_verified = True
            user.save()
            
            return Response({
                'message': _('Email verified successfully. You can now log in.')
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': _('Invalid or expired token')
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    def _verify_token(self, token):
        """
        Verify the email verification token.
        """
        # Implementation depends on your token storage
        # For simplicity, we'll just return None here
        return None

