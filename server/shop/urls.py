from django.urls import path

# User endpoints
urlpatterns = [
    path('signup/', __import__('{}.views'.format(__package__), fromlist=['UserSignupView']).UserSignupView.as_view(), name='signup_user'),
    path('login/', __import__('{}.views'.format(__package__), fromlist=['UserLoginView']).UserLoginView.as_view(), name='login_user'),
    path('forgot-password/', __import__('{}.views'.format(__package__), fromlist=['UserForgotPasswordView']).UserForgotPasswordView.as_view(), name='forgot_password_user'),
    path('reset-password/', __import__('{}.views'.format(__package__), fromlist=['UserResetPasswordView']).UserResetPasswordView.as_view(), name='reset_password_user'),
    path('profile/', __import__('{}.views'.format(__package__), fromlist=['ProfileView']).ProfileView.as_view(), name='profile_user'),
    path('kyc-update/', __import__('{}.views'.format(__package__), fromlist=['KYCUpdateView']).KYCUpdateView.as_view(), name='kyc_update_user'),

    # Common endpoints
    path('logout/', __import__('{}.views'.format(__package__), fromlist=['LogoutView']).LogoutView.as_view(), name='logout'),
    path('change-password/', __import__('{}.views'.format(__package__), fromlist=['ChangePasswordView']).ChangePasswordView.as_view(), name='change_password'),
    path('verify-email/', __import__('{}.views'.format(__package__), fromlist=['CommonVerifyEmailView']).CommonVerifyEmailView.as_view(), name='verify_email'),
    path('resend-code/', __import__('{}.views'.format(__package__), fromlist=['ResendVerificationCodeView']).ResendVerificationCodeView.as_view(), name='resend_code'),
]
