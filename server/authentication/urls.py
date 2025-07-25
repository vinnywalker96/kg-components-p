from django.urls import path
from .views import (
    UserRegistrationView,
    UserLoginView,
    AdminLoginView,
    CustomTokenRefreshView,
    LogoutView,
    EmailVerificationView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    UserProfileView
)

app_name = 'authentication'

urlpatterns = [
    # Authentication endpoints
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('admin/login/', AdminLoginView.as_view(), name='admin-login'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Email verification
    path('verify-email/', EmailVerificationView.as_view(), name='verify-email'),
    
    # Password reset
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # User profile
    path('profile/', UserProfileView.as_view(), name='user-profile'),
]

