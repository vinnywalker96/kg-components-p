from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
import json

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
        
        # Create a regular user
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
        
        # URLs
        self.register_url = reverse('authentication:user-register')
        self.login_url = reverse('authentication:user-login')
        self.admin_login_url = reverse('authentication:admin-login')
        self.token_refresh_url = reverse('authentication:token-refresh')
        self.logout_url = reverse('authentication:logout')
    
    def test_user_registration(self):
        """
        Test user registration.
        """
        data = {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'newpassword123',
            'password_confirm': 'newpassword123'
        }
        
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())
    
    def test_user_registration_password_mismatch(self):
        """
        Test user registration with mismatched passwords.
        """
        data = {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'newpassword123',
            'password_confirm': 'differentpassword'
        }
        
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email='newuser@example.com').exists())
    
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
    
    def test_non_admin_login_to_admin(self):
        """
        Test non-admin user trying to login to admin endpoint.
        """
        data = {
            'email': 'user@example.com',
            'password': 'testpassword123'
        }
        
        response = self.client.post(self.admin_login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_token_refresh(self):
        """
        Test token refresh.
        """
        # First login to get a refresh token
        login_data = {
            'email': 'user@example.com',
            'password': 'testpassword123'
        }
        
        login_response = self.client.post(self.login_url, login_data, format='json')
        refresh_token = login_response.data['refresh']
        
        # Then use the refresh token to get a new access token
        refresh_data = {
            'refresh': refresh_token
        }
        
        response = self.client.post(self.token_refresh_url, refresh_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_logout(self):
        """
        Test user logout.
        """
        # First login to get a refresh token
        login_data = {
            'email': 'user@example.com',
            'password': 'testpassword123'
        }
        
        login_response = self.client.post(self.login_url, login_data, format='json')
        refresh_token = login_response.data['refresh']
        access_token = login_response.data['access']
        
        # Set the authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Then logout
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

