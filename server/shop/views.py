import logging
from datetime import timedelta

from django.utils.timezone import now
from django.contrib.auth.hashers import check_password
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,generics,permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import IntegrityError
from drf_yasg.utils import swagger_auto_schema
##from .swagger_params import token_param, first_name_param, last_name_param, physical_address_param, phone_number_param, profile_pic_param, user_kyc_schema,  driver_kyc_schema
from drf_yasg import openapi

from .models import  User, Driver, OTP
from .serializers import (
    UserSignupSerializer,
    EmailVerificationSerializer,
    UserLoginSerializer,
    ResendOTPSerializer,
    UserProfileSerializer,
)
from .utils import generate_otp, send_password_reset_otp_email, send_verification_otp_email, send_kyc_submission_email
logger = logging.getLogger(__name__)

###############################################################################
# Base Views for Signup, Login, Forgot & Reset Password
###############################################################################

class BaseSignupView(APIView):
    serializer_class = None
    permission_classes = []  # Allow unauthenticated access

    success_message = "Signup successful. Check your email for OTP."

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                # Generate OTP
                otp_code = generate_otp()
                # Create OTP instance
                if isinstance(user, User):
                    OTP.objects.create(user=user, code=otp_code)
                elif isinstance(user, Driver):
                    OTP.objects.create(driver=user, code=otp_code)
                else:
                    return Response({"error": "Invalid user type."}, status=status.HTTP_400_BAD_REQUEST)
                # Send OTP via email
                email_sent = send_verification_otp_email(user.email, otp_code)
                if email_sent:
                    return Response({"message": self.success_message}, status=status.HTTP_201_CREATED)
                else:
                    return Response({"error": "Failed to send OTP email. Please try again."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except IntegrityError:
                return Response({"error": "An account with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BaseLoginView(APIView):
    """
    Base view for handling login.
    Expects a serializer_class attribute that validates and returns a user.
    """
    serializer_class = None
    permission_classes = []  # Allow unauthenticated access

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BaseForgotPasswordView(APIView):
    """
    Base view for handling forgot password.
    Expects a model_class attribute (User or Driver) that has an OTP relation.
    """
    model_class = None
    permission_classes = []  # Allow unauthenticated access


    def post(self, request):
        email = request.data.get("email")
        try:
            obj = self.model_class.objects.get(email=email)
            reset_otp = generate_otp()
            # For User or Driver, update the OTP instance accordingly.
            if isinstance(obj, User):
                otp_instance, created = OTP.objects.get_or_create(user=obj)
            elif isinstance(obj, Driver):
                otp_instance, created = OTP.objects.get_or_create(driver=obj)
            else:
                return Response({"error": "Invalid object type."},
                                status=status.HTTP_400_BAD_REQUEST)
            otp_instance.code = reset_otp
            # Update created_at manually since auto_now_add doesn't update on save.
            otp_instance.created_at = now()
            otp_instance.is_verified = False
            otp_instance.save()
            send_password_reset_otp_email(obj.email, reset_otp, validity_minutes=60)
            return Response({"message": "OTP sent to email for password reset."},
                            status=status.HTTP_200_OK)
        except self.model_class.DoesNotExist:
            return Response({"error": "User not found."},
                            status=status.HTTP_404_NOT_FOUND)

class BaseResetPasswordView(APIView):
    """
    Base view for handling password reset using OTP.
    Expects a model_class attribute (User or Driver) with an OTP relation.
    """
    model_class = None

    def post(self, request):
        email = request.data.get("email")
        provided_otp = request.data.get("otp")
        new_password = request.data.get("new_password")
        try:
            obj = self.model_class.objects.get(email=email)
            try:
                otp_instance = obj.otp
            except Exception:
                return Response({"error": "OTP not found for this user."},
                                status=status.HTTP_400_BAD_REQUEST)
            # Set OTP validity to 60 minutes.
            otp_validity_duration = timedelta(minutes=60)
            if otp_instance.code != provided_otp or (now() - otp_instance.created_at) > otp_validity_duration:
                return Response({"error": "Invalid or expired OTP."},
                                status=status.HTTP_400_BAD_REQUEST)
            obj.set_password(new_password)
            otp_instance.delete()  # Clear OTP after successful reset
            obj.save()
            return Response({"message": "Password reset successful."},
                            status=status.HTTP_200_OK)
        except self.model_class.DoesNotExist:
            return Response({"error": "User not found."},
                            status=status.HTTP_404_NOT_FOUND)


###############################################################################
# User Endpoints
###############################################################################

class UserSignupView(BaseSignupView):
    serializer_class = UserSignupSerializer
    success_message = "User signup successful. Check your email for OTP."

    @swagger_auto_schema(
        request_body=UserSignupSerializer,
        responses={
            201: "Signup successful. Check your email for OTP.",
            400: "Invalid input or user already exists."
        }
    )
    def post(self, request):
        return super().post(request)


class UserLoginView(BaseLoginView):
    serializer_class = UserLoginSerializer

    @swagger_auto_schema(
        request_body=UserLoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful. Returns JWT tokens.",
                examples={"application/json": {
                    "refresh": "refresh_token_here",
                    "access": "access_token_here"
                }}
            ),
            400: "Invalid email or password."
        }
    )
    def post(self, request):
        return super().post(request)


class UserForgotPasswordView(BaseForgotPasswordView):
    model_class = User

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description="User email")
            },
            required=['email']
        ),
        responses={200: "OTP sent to email for password reset.", 404: "User not found."}
    )
    def post(self, request):
        return super().post(request)


class UserResetPasswordView(BaseResetPasswordView):
    model_class = User
    permission_classes = []

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description="User email"),
                'otp': openapi.Schema(type=openapi.TYPE_STRING, description="OTP received via email"),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, description="New password"),
            },
            required=['email', 'otp', 'new_password']
        ),
        responses={
            200: "Password reset successful.",
            400: "Invalid or expired OTP.",
            404: "User not found."
        }
    )
    def post(self, request):
        return super().post(request)


class ProfileView(APIView):
    """
    Endpoint for client users to retrieve and update their profile.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{'Bearer': []}],
        responses={200: UserProfileSerializer()}
    )
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    @swagger_auto_schema(
        security=[{'Bearer': []}],
        responses={200: UserProfileSerializer()}
    )
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        security=[{'Bearer': []}],

        request_body=UserProfileSerializer,
        responses={
            200: "Profile updated successfully.",
            400: "Invalid input."
        }
    )
    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated successfully."},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class LogoutView(APIView):
    """
    Endpoint to logout an authenticated user (client or driver) by blacklisting the refresh token.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh_token': openapi.Schema(type=openapi.TYPE_STRING, description="Refresh token")
            },
            required=['refresh_token']
        ),
        responses={
            200: "Logout successful.",
            400: "Invalid token or already blacklisted."
        }
    )
    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response({"error": "Refresh token is required."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful."},
                            status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Invalid token or already blacklisted."},
                            status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    Endpoint for authenticated users (client or driver) to change their password.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'old_password': openapi.Schema(type=openapi.TYPE_STRING, description="Current password"),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, description="New password"),
            },
            required=['old_password', 'new_password']
        ),
        responses={
            200: "Password changed successfully.",
            400: "Invalid old password or input."
        }
    )
    def post(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        if not check_password(old_password, user.password):
            return Response({"error": "Old password is incorrect."},
                            status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({"message": "Password changed successfully."},
                        status=status.HTTP_200_OK)


class CommonVerifyEmailView(APIView):
    permission_classes = []  # No auth required

    """
    Common endpoint to verify a user's email (for both client users and drivers).
    Expects 'email' and 'otp' in the request. Returns JWT tokens on success.
    """

    def get_tokens_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description="User email"),
                'otp': openapi.Schema(type=openapi.TYPE_STRING, description="OTP code")
            },
            required=['email', 'otp']
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(type=openapi.TYPE_STRING),
                    "access": openapi.Schema(type=openapi.TYPE_STRING),
                    "refresh": openapi.Schema(type=openapi.TYPE_STRING),
                }
            ),
            400: "Invalid or expired OTP, or email not found."
        }
    )
    def post(self, request):
        email = request.data.get("email")
        otp_input = request.data.get("otp")

        if not email or not otp_input:
            return Response({"error": "Email and OTP are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Try to find the user in User model; else check Driver.
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            try:
                user_obj = Driver.objects.get(email=email)
            except Driver.DoesNotExist:
                return Response({"error": "User not found."},
                                status=status.HTTP_404_NOT_FOUND)

        # Ensure OTP instance exists
        try:
            otp_instance = user_obj.otp
        except Exception:
            return Response({"error": "No OTP found for this user."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Validate OTP
        otp_validity_duration = timedelta(minutes=60)
        if otp_instance.code != otp_input or (now() - otp_instance.created_at) > otp_validity_duration:
            return Response({"error": "Invalid or expired OTP."},
                            status=status.HTTP_400_BAD_REQUEST)

        # OTP is valid — activate user and delete OTP
        user_obj.is_active = True
        otp_instance.delete()
        user_obj.save()

        # Return JWT tokens
        tokens = self.get_tokens_for_user(user_obj)

        return Response({
            "message": "Email verified successfully.",
            "access": tokens["access"],
            "refresh": tokens["refresh"]
        }, status=status.HTTP_200_OK)



class ResendVerificationCodeView(APIView):
    permission_classes = []
    """
    Common endpoint to resend the verification OTP code for email verification
    for both client users and drivers. Expects 'email' in the request.
    """
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description="User email")
            },
            required=['email']
        ),
        responses={
            200: "Verification code resent successfully.",
            404: "User not found."
        }
    )
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required."},
                            status=status.HTTP_400_BAD_REQUEST)
        
        # Try to find the user in either the User or Driver models.
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            try:
                user_obj = Driver.objects.get(email=email)
            except Driver.DoesNotExist:
                return Response({"error": "User not found."},
                                status=status.HTTP_404_NOT_FOUND)
        
        # Generate a new OTP code.
        new_otp_code = generate_otp()
        # Get or create the OTP instance for the user.
        otp_instance, created = OTP.objects.get_or_create(user=user_obj)
        otp_instance.code = new_otp_code
        # Update the creation timestamp (since auto_now_add doesn't update on save).
        otp_instance.created_at = now()
        otp_instance.is_verified = False
        otp_instance.save()
        
        # Send the OTP email with a validity of 60 minutes.
        email_sent = send_verification_otp_email(user_obj.email, new_otp_code, validity_minutes=60)
        if email_sent:
            return Response({"message": "Verification code resent successfully."},
                            status=status.HTTP_200_OK)
        else:
            return Response({"error": "Failed to send verification email."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# Authorization parameter
token_param = openapi.Parameter(
    'Authorization', openapi.IN_HEADER,
    description="Bearer token for authentication",
    type=openapi.TYPE_STRING,
    required=True
)

