from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import (
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    PasswordChangeSerializer,
    AdminUserListSerializer,
    AdminUserDetailSerializer,
    AdminUserUpdateSerializer
)
from authentication.permissions import IsAdmin, IsAuthenticatedAndVerified

User = get_user_model()

class UserProfileView(generics.RetrieveAPIView):
    """
    API endpoint for retrieving the authenticated user's profile.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticatedAndVerified]
    
    def get_object(self):
        return self.request.user


class UserProfileUpdateView(generics.UpdateAPIView):
    """
    API endpoint for updating the authenticated user's profile.
    """
    serializer_class = UserProfileUpdateSerializer
    permission_classes = [IsAuthenticatedAndVerified]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return the updated profile using the profile serializer
        profile_serializer = UserProfileSerializer(instance)
        return Response(profile_serializer.data)


class PasswordChangeView(APIView):
    """
    API endpoint for changing the authenticated user's password.
    """
    permission_classes = [IsAuthenticatedAndVerified]
    
    @swagger_auto_schema(
        request_body=PasswordChangeSerializer,
        responses={
            200: openapi.Response(
                description="Password changed successfully",
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
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': _('Password changed successfully')
        }, status=status.HTTP_200_OK)


# Admin views for user management

class AdminUserListView(generics.ListAPIView):
    """
    API endpoint for listing all users (admin only).
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = AdminUserListSerializer
    permission_classes = [IsAdmin]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by email if provided
        email = self.request.query_params.get('email', None)
        if email:
            queryset = queryset.filter(email__icontains=email)
        
        # Filter by active status if provided
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        # Filter by verified status if provided
        is_verified = self.request.query_params.get('is_verified', None)
        if is_verified is not None:
            is_verified = is_verified.lower() == 'true'
            queryset = queryset.filter(is_verified=is_verified)
        
        return queryset


class AdminUserDetailView(generics.RetrieveAPIView):
    """
    API endpoint for retrieving detailed user information (admin only).
    """
    queryset = User.objects.all()
    serializer_class = AdminUserDetailSerializer
    permission_classes = [IsAdmin]
    lookup_field = 'id'


class AdminUserUpdateView(generics.UpdateAPIView):
    """
    API endpoint for updating user information (admin only).
    """
    queryset = User.objects.all()
    serializer_class = AdminUserUpdateSerializer
    permission_classes = [IsAdmin]
    lookup_field = 'id'
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return the updated user using the detail serializer
        detail_serializer = AdminUserDetailSerializer(instance)
        return Response(detail_serializer.data)


class AdminUserActivateView(APIView):
    """
    API endpoint for activating or deactivating a user (admin only).
    """
    permission_classes = [IsAdmin]
    
    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="User status updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                    }
                )
            ),
            404: "User not found"
        }
    )
    def post(self, request, id):
        user = get_object_or_404(User, id=id)
        
        # Toggle the active status
        user.is_active = not user.is_active
        user.save()
        
        return Response({
            'message': _('User status updated successfully'),
            'is_active': user.is_active
        }, status=status.HTTP_200_OK)


class AdminUserVerifyView(APIView):
    """
    API endpoint for manually verifying a user (admin only).
    """
    permission_classes = [IsAdmin]
    
    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="User verification status updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'is_verified': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                    }
                )
            ),
            404: "User not found"
        }
    )
    def post(self, request, id):
        user = get_object_or_404(User, id=id)
        
        # Toggle the verified status
        user.is_verified = not user.is_verified
        
        # If verifying the user, also activate them
        if user.is_verified and not user.is_active:
            user.is_active = True
            
        user.save()
        
        return Response({
            'message': _('User verification status updated successfully'),
            'is_verified': user.is_verified,
            'is_active': user.is_active
        }, status=status.HTTP_200_OK)

