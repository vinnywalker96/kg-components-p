from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
import json

from .models import Product, Order, OrderItem, Sale

User = get_user_model()

class ShopTests(TestCase):
    """
    Test cases for shop endpoints.
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
        
        # Create some products
        self.product1 = Product.objects.create(
            sku_code='SKU001',
            name='Test Product 1',
            description='This is a test product',
            price=Decimal('19.99')
        )
        
        self.product2 = Product.objects.create(
            sku_code='SKU002',
            name='Test Product 2',
            description='This is another test product',
            price=Decimal('29.99')
        )
        
        # Create an order
        self.order = Order.objects.create(
            user=self.user,
            status='pending'
        )
        
        # Create order items
        self.order_item1 = OrderItem.objects.create(
            order=self.order,
            product=self.product1,
            quantity=2,
            price=self.product1.price
        )
        
        self.order_item2 = OrderItem.objects.create(
            order=self.order,
            product=self.product2,
            quantity=1,
            price=self.product2.price
        )
        
        # URLs
        self.product_list_url = reverse('shop:product-list')
        self.product_detail_url = reverse('shop:product-detail', args=[str(self.product1.id)])
        self.product_create_url = reverse('shop:product-create')
        self.product_update_url = reverse('shop:product-update', args=[str(self.product1.id)])
        self.product_delete_url = reverse('shop:product-delete', args=[str(self.product1.id)])
        
        self.order_list_url = reverse('shop:order-list')
        self.order_detail_url = reverse('shop:order-detail', args=[str(self.order.id)])
        self.order_create_url = reverse('shop:order-create')
        self.order_update_url = reverse('shop:order-update', args=[str(self.order.id)])
        
        self.sale_list_url = reverse('shop:sale-list')
        self.sales_analytics_url = reverse('shop:sales-analytics')
        self.product_analytics_url = reverse('shop:product-analytics')
        
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
    
    def test_product_list(self):
        """
        Test listing products.
        """
        response = self.client.get(self.product_list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_product_detail(self):
        """
        Test retrieving product details.
        """
        response = self.client.get(self.product_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Product 1')
        self.assertEqual(response.data['sku_code'], 'SKU001')
        self.assertEqual(Decimal(response.data['price']), Decimal('19.99'))
    
    def test_product_create(self):
        """
        Test creating a product (admin only).
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        data = {
            'sku_code': 'SKU003',
            'name': 'New Product',
            'description': 'This is a new product',
            'price': '39.99'
        }
        
        response = self.client.post(self.product_create_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 3)
        
        # Verify the product was created correctly
        product = Product.objects.get(sku_code='SKU003')
        self.assertEqual(product.name, 'New Product')
        self.assertEqual(product.price, Decimal('39.99'))
    
    def test_product_update(self):
        """
        Test updating a product (admin only).
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        data = {
            'name': 'Updated Product',
            'price': '24.99'
        }
        
        response = self.client.patch(self.product_update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the product was updated correctly
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.name, 'Updated Product')
        self.assertEqual(self.product1.price, Decimal('24.99'))
    
    def test_product_delete(self):
        """
        Test deleting a product (admin only).
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        response = self.client.delete(self.product_delete_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.count(), 1)
        self.assertFalse(Product.objects.filter(id=self.product1.id).exists())
    
    def test_order_list(self):
        """
        Test listing orders.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')
        
        response = self.client.get(self.order_list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_order_detail(self):
        """
        Test retrieving order details.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')
        
        response = self.client.get(self.order_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'pending')
        self.assertEqual(len(response.data['items']), 2)
    
    def test_order_create(self):
        """
        Test creating an order.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')
        
        data = {
            'status': 'pending',
            'items': [
                {
                    'product_id': str(self.product1.id),
                    'quantity': 3
                },
                {
                    'product_id': str(self.product2.id),
                    'quantity': 2
                }
            ]
        }
        
        response = self.client.post(self.order_create_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 2)
        
        # Verify the order was created correctly
        new_order = Order.objects.latest('created_at')
        self.assertEqual(new_order.status, 'pending')
        self.assertEqual(new_order.user, self.user)
        self.assertEqual(new_order.orderitem_set.count(), 2)
    
    def test_order_update(self):
        """
        Test updating an order.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')
        
        data = {
            'status': 'completed'
        }
        
        response = self.client.patch(self.order_update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the order was updated correctly
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'completed')
        
        # Verify a sale record was created
        self.assertEqual(Sale.objects.count(), 1)
        sale = Sale.objects.first()
        self.assertEqual(sale.order, self.order)
        self.assertEqual(sale.total_amount, Decimal('19.99') * 2 + Decimal('29.99'))
    
    def test_sale_list(self):
        """
        Test listing sales (admin only).
        """
        # First, create a completed order to generate a sale
        self.order.status = 'completed'
        self.order.save()
        
        # Create a sale record
        Sale.objects.create(
            order=self.order,
            total_amount=Decimal('19.99') * 2 + Decimal('29.99')
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        response = self.client.get(self.sale_list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_sales_analytics(self):
        """
        Test sales analytics (admin only).
        """
        # First, create a completed order to generate a sale
        self.order.status = 'completed'
        self.order.save()
        
        # Create a sale record
        Sale.objects.create(
            order=self.order,
            total_amount=Decimal('19.99') * 2 + Decimal('29.99')
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        response = self.client.get(self.sales_analytics_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_orders'], 1)
        self.assertEqual(Decimal(response.data['total_sales']), Decimal('19.99') * 2 + Decimal('29.99'))
    
    def test_product_analytics(self):
        """
        Test product analytics (admin only).
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        response = self.client.get(self.product_analytics_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('top_products', response.data)

