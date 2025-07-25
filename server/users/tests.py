from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
import json

User = get_user_model()

class UserProfileTests(TestCase):
    """
    Test cases for user profile endpoints.
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
        self.profile_url = reverse('users:profile')
        self.profile_update_url = reverse('users:profile-update')
        self.password_change_url = reverse('users:password-change')
        
        # Admin URLs
        self.admin_user_list_url = reverse('users:admin-user-list')
        self.admin_user_detail_url = reverse('users:admin-user-detail', args=[str(self.user.id)])
        self.admin_user_update_url = reverse('users:admin-user-update', args=[str(self.user.id)])
        self.admin_user_activate_url = reverse('users:admin-user-activate', args=[str(self.user.id)])
        self.admin_user_verify_url = reverse('users:admin-user-verify', args=[str(self.user.id)])
        
        # Login the user to get tokens
        login_data = {
            'email': 'user@example.com',
            'password': 'testpassword123'
        }
        
        login_url = reverse('authentication:user-login')
        login_response = self.client.post(login_url, login_data, format='json')
        self.user_token = login_response.data['access']
        
        # Login the admin to get tokens
        admin_login_data = {
            'email': 'admin@example.com',
            'password': 'adminpassword123'
        }
        
        admin_login_url = reverse('authentication:admin-login')
        admin_login_response = self.client.post(admin_login_url, admin_login_data, format='json')
        self.admin_token = admin_login_response.data['access']
    
    def test_get_profile(self):
        """
        Test retrieving user profile.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'user@example.com')
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['last_name'], 'User')
    
    def test_update_profile(self):
        """
        Test updating user profile.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')
        
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        
        response = self.client.patch(self.profile_update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        self.assertEqual(response.data['last_name'], 'Name')
        
        # Verify the changes in the database
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
    
    def test_change_password(self):
        """
        Test changing user password.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')
        
        data = {
            'current_password': 'testpassword123',
            'new_password': 'newpassword456',
            'confirm_password': 'newpassword456'
        }
        
        response = self.client.post(self.password_change_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the password was changed by trying to login with the new password
        self.client.credentials()  # Clear credentials
        
        login_data = {
            'email': 'user@example.com',
            'password': 'newpassword456'
        }
        
        login_url = reverse('authentication:user-login')
        login_response = self.client.post(login_url, login_data, format='json')
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', login_response.data)
    
    def test_admin_user_list(self):
        """
        Test admin listing all users.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        response = self.client.get(self.admin_user_list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Two users: regular and admin
    
    def test_admin_user_detail(self):
        """
        Test admin viewing user details.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        response = self.client.get(self.admin_user_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'user@example.com')
    
    def test_admin_user_update(self):
        """
        Test admin updating user information.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        data = {
            'first_name': 'Admin',
            'last_name': 'Updated',
            'is_active': True
        }
        
        response = self.client.patch(self.admin_user_update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Admin')
        self.assertEqual(response.data['last_name'], 'Updated')
        self.assertTrue(response.data['is_active'])
        
        # Verify the changes in the database
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Admin')
        self.assertEqual(self.user.last_name, 'Updated')
        self.assertTrue(self.user.is_active)
    
    def test_admin_user_activate(self):
        """
        Test admin activating/deactivating a user.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        # Deactivate the user
        response = self.client.post(self.admin_user_activate_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_active'])
        
        # Verify the change in the database
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        
        # Activate the user again
        response = self.client.post(self.admin_user_activate_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_active'])
        
        # Verify the change in the database
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
    
    def test_admin_user_verify(self):
        """
        Test admin verifying a user.
        """
        # First, set the user as unverified
        self.user.is_verified = False
        self.user.save()
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        # Verify the user
        response = self.client.post(self.admin_user_verify_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_verified'])
        
        # Verify the change in the database
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_verified)
        
        # Unverify the user
        response = self.client.post(self.admin_user_verify_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_verified'])
        
        # Verify the change in the database
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_verified)

