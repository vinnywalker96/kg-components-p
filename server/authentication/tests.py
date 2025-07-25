from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
import uuid
from django.utils import timezone

User = get_user_model()

class AuthenticationTests(TestCase):
    """
    Test cases for authentication endpoints.
    """
    
    def setUp(self):
        """
        Set up test data.
        """
        self.client = APIClient()
        
        # Create a verified user
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User',
            is_active=True,
            is_verified=True
        )
        
        # Create an admin user
        self.admin = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpassword123',
            first_name='Admin',
            last_name='User'
        )
        
        # Create an unverified user
        self.unverified_user = User.objects.create_user(
            email='unverified@example.com',
            password='testpassword123',
            first_name='Unverified',
            last_name='User',
            is_active=True,
            is_verified=False
        )
        
        # URLs
        self.register_url = reverse('authentication:user-register')
        self.login_url = reverse('authentication:user-login')
        self.admin_login_url = reverse('authentication:admin-login')
        self.token_refresh_url = reverse('authentication:token-refresh')
        self.logout_url = reverse('authentication:logout')
        self.verify_email_url = reverse('authentication:verify-email')
        self.password_reset_url = reverse('authentication:password-reset-request')
        self.password_reset_confirm_url = reverse('authentication:password-reset-confirm')
        self.profile_url = reverse('authentication:user-profile')
    
    def test_user_registration(self):
        """
        Test user registration.
        """
        data = {
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'password_confirm': 'newpassword123',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())
    
    def test_user_login(self):
        """
        Test user login.
        """
        data = {
            'email': 'user@example.com',
            'password': 'testpassword123'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['email'], 'user@example.com')
    
    def test_admin_login(self):
        """
        Test admin login.
        """
        data = {
            'email': 'admin@example.com',
            'password': 'adminpassword123'
        }
        
        response = self.client.post(self.admin_login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['email'], 'admin@example.com')
        self.assertTrue(response.data['is_admin'])
    
    def test_unverified_user_login(self):
        """
        Test login with unverified user.
        """
        data = {
            'email': 'unverified@example.com',
            'password': 'testpassword123'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_token_refresh(self):
        """
        Test token refresh.
        """
        # First, login to get a refresh token
        login_data = {
            'email': 'user@example.com',
            'password': 'testpassword123'
        }
        
        login_response = self.client.post(self.login_url, login_data, format='json')
        refresh_token = login_response.data['refresh']
        
        # Then, use the refresh token to get a new access token
        refresh_data = {
            'refresh': refresh_token
        }
        
        response = self.client.post(self.token_refresh_url, refresh_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_logout(self):
        """
        Test logout.
        """
        # First, login to get a refresh token
        login_data = {
            'email': 'user@example.com',
            'password': 'testpassword123'
        }
        
        login_response = self.client.post(self.login_url, login_data, format='json')
        refresh_token = login_response.data['refresh']
        access_token = login_response.data['access']
        
        # Set the authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Then, logout
        logout_data = {
            'refresh': refresh_token
        }
        
        response = self.client.post(self.logout_url, logout_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Try to use the refresh token again (should fail)
        refresh_data = {
            'refresh': refresh_token
        }
        
        response = self.client.post(self.token_refresh_url, refresh_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_email_verification(self):
        """
        Test email verification.
        """
        # Create a user with a verification token
        user = User.objects.create_user(
            email='verify@example.com',
            password='testpassword123',
            first_name='Verify',
            last_name='User',
            is_active=False,
            is_verified=False
        )
        
        token = str(uuid.uuid4())
        user.verification_token = token
        user.verification_token_created_at = timezone.now()
        user.save()
        
        # Verify the email
        data = {
            'token': token
        }
        
        response = self.client.post(self.verify_email_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if the user is now verified and active
        user.refresh_from_db()
        self.assertTrue(user.is_verified)
        self.assertTrue(user.is_active)
        self.assertIsNone(user.verification_token)
    
    def test_password_reset_request(self):
        """
        Test password reset request.
        """
        data = {
            'email': 'user@example.com'
        }
        
        response = self.client.post(self.password_reset_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if the user has a reset token
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.reset_password_token)
        self.assertIsNotNone(self.user.reset_password_token_created_at)
    
    def test_password_reset_confirm(self):
        """
        Test password reset confirmation.
        """
        # Set a reset token for the user
        token = str(uuid.uuid4())
        self.user.reset_password_token = token
        self.user.reset_password_token_created_at = timezone.now()
        self.user.save()
        
        # Reset the password
        data = {
            'token': token,
            'password': 'newpassword123',
            'password_confirm': 'newpassword123'
        }
        
        response = self.client.post(self.password_reset_confirm_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if the user's password has been changed
        self.user.refresh_from_db()
        self.assertIsNone(self.user.reset_password_token)
        self.assertTrue(self.user.check_password('newpassword123'))
    
    def test_user_profile(self):
        """
        Test user profile.
        """
        # Login
        login_data = {
            'email': 'user@example.com',
            'password': 'testpassword123'
        }
        
        login_response = self.client.post(self.login_url, login_data, format='json')
        access_token = login_response.data['access']
        
        # Set the authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Get the profile
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'user@example.com')
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['last_name'], 'User')
        
        # Update the profile
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'physical_address': '123 Test St, Test City'
        }
        
        response = self.client.patch(self.profile_url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if the profile has been updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.physical_address, '123 Test St, Test City')

