from django.urls import path
from .views import (
    UserProfileView,
    UserProfileUpdateView,
    PasswordChangeView,
    AdminUserListView,
    AdminUserDetailView,
    AdminUserUpdateView,
    AdminUserActivateView,
    AdminUserVerifyView
)

app_name = 'users'

urlpatterns = [
    # User profile endpoints
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('profile/update/', UserProfileUpdateView.as_view(), name='profile-update'),
    path('password/change/', PasswordChangeView.as_view(), name='password-change'),
    
    # Admin user management endpoints
    path('admin/users/', AdminUserListView.as_view(), name='admin-user-list'),
    path('admin/users/<uuid:id>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('admin/users/<uuid:id>/update/', AdminUserUpdateView.as_view(), name='admin-user-update'),
    path('admin/users/<uuid:id>/activate/', AdminUserActivateView.as_view(), name='admin-user-activate'),
    path('admin/users/<uuid:id>/verify/', AdminUserVerifyView.as_view(), name='admin-user-verify'),
]

