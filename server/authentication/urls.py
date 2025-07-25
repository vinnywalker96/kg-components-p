from django.urls import path
from .views import (
    UserRegistrationView,
    AdminRegistrationView,
    UserLoginView,
    AdminLoginView,
    CustomTokenRefreshView,
    LogoutView,
    LogoutAllView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    EmailVerificationView
)

app_name = 'authentication'

urlpatterns = [
    # User authentication endpoints
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('logout-all/', LogoutAllView.as_view(), name='logout-all'),
    path('password-reset/request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('email-verify/', EmailVerificationView.as_view(), name='email-verify'),
    
    # Admin authentication endpoints
    path('admin/register/', AdminRegistrationView.as_view(), name='admin-register'),
    path('admin/login/', AdminLoginView.as_view(), name='admin-login'),
]

