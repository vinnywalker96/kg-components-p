from rest_framework import generics, status, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Count
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Product, Order, OrderItem, Sale
from .serializers import (
    ProductSerializer,
    ProductCreateUpdateSerializer,
    OrderSerializer,
    OrderCreateSerializer,
    OrderUpdateSerializer,
    SaleSerializer
)
from authentication.permissions import IsAdmin, IsOwnerOrAdmin, IsAuthenticatedAndVerified

# Product views

class ProductListView(generics.ListAPIView):
    """
    API endpoint for listing products.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['price']
    search_fields = ['name', 'description', 'sku_code']
    ordering_fields = ['name', 'price']
    ordering = ['name']


class ProductDetailView(generics.RetrieveAPIView):
    """
    API endpoint for retrieving product details.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'


class ProductCreateView(generics.CreateAPIView):
    """
    API endpoint for creating products (admin only).
    """
    serializer_class = ProductCreateUpdateSerializer
    permission_classes = [IsAdmin]


class ProductUpdateView(generics.UpdateAPIView):
    """
    API endpoint for updating products (admin only).
    """
    queryset = Product.objects.all()
    serializer_class = ProductCreateUpdateSerializer
    permission_classes = [IsAdmin]
    lookup_field = 'id'


class ProductDeleteView(generics.DestroyAPIView):
    """
    API endpoint for deleting products (admin only).
    """
    queryset = Product.objects.all()
    permission_classes = [IsAdmin]
    lookup_field = 'id'


# Order views

class OrderListView(generics.ListAPIView):
    """
    API endpoint for listing orders.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticatedAndVerified]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Return orders for the current user, or all orders for admins.
        """
        user = self.request.user
        if user.is_staff:
            return Order.objects.all().prefetch_related('orderitem_set', 'orderitem_set__product')
        return Order.objects.filter(user=user).prefetch_related('orderitem_set', 'orderitem_set__product')


class OrderDetailView(generics.RetrieveAPIView):
    """
    API endpoint for retrieving order details.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticatedAndVerified, IsOwnerOrAdmin]
    lookup_field = 'id'
    
    def get_queryset(self):
        """
        Return orders for the current user, or all orders for admins.
        """
        user = self.request.user
        if user.is_staff:
            return Order.objects.all().prefetch_related('orderitem_set', 'orderitem_set__product')
        return Order.objects.filter(user=user).prefetch_related('orderitem_set', 'orderitem_set__product')


class OrderCreateView(generics.CreateAPIView):
    """
    API endpoint for creating orders.
    """
    serializer_class = OrderCreateSerializer
    permission_classes = [IsAuthenticatedAndVerified]
    
    def perform_create(self, serializer):
        serializer.save()


class OrderUpdateView(generics.UpdateAPIView):
    """
    API endpoint for updating orders.
    """
    serializer_class = OrderUpdateSerializer
    permission_classes = [IsAuthenticatedAndVerified, IsOwnerOrAdmin]
    lookup_field = 'id'
    
    def get_queryset(self):
        """
        Return orders for the current user, or all orders for admins.
        """
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=user)


# Sale views (admin only)

class SaleListView(generics.ListAPIView):
    """
    API endpoint for listing sales (admin only).
    """
    queryset = Sale.objects.all().select_related('order', 'order__user')
    serializer_class = SaleSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['sale_date', 'total_amount']
    ordering = ['-sale_date']


class SaleDetailView(generics.RetrieveAPIView):
    """
    API endpoint for retrieving sale details (admin only).
    """
    queryset = Sale.objects.all().select_related('order', 'order__user')
    serializer_class = SaleSerializer
    permission_classes = [IsAdmin]
    lookup_field = 'id'


# Analytics views (admin only)

class SalesAnalyticsView(APIView):
    """
    API endpoint for sales analytics (admin only).
    """
    permission_classes = [IsAdmin]
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'period',
                openapi.IN_QUERY,
                description="Period for analytics (daily, weekly, monthly, yearly)",
                type=openapi.TYPE_STRING,
                enum=['daily', 'weekly', 'monthly', 'yearly'],
                default='monthly'
            )
        ],
        responses={
            200: openapi.Response(
                description="Sales analytics",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total_sales': openapi.Schema(type=openapi.TYPE_NUMBER),
                        'total_orders': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'average_order_value': openapi.Schema(type=openapi.TYPE_NUMBER)
                    }
                )
            )
        }
    )
    def get(self, request):
        period = request.query_params.get('period', 'monthly')
        
        # Calculate the start date based on the period
        now = timezone.now()
        if period == 'daily':
            start_date = now - timedelta(days=1)
        elif period == 'weekly':
            start_date = now - timedelta(weeks=1)
        elif period == 'yearly':
            start_date = now - timedelta(days=365)
        else:  # monthly (default)
            start_date = now - timedelta(days=30)
        
        # Get sales data for the period
        sales = Sale.objects.filter(sale_date__gte=start_date)
        
        # Calculate analytics
        total_sales = sales.aggregate(total=Sum('total_amount'))['total'] or 0
        total_orders = sales.count()
        average_order_value = total_sales / total_orders if total_orders > 0 else 0
        
        return Response({
            'total_sales': total_sales,
            'total_orders': total_orders,
            'average_order_value': average_order_value,
            'period': period
        })


class ProductAnalyticsView(APIView):
    """
    API endpoint for product analytics (admin only).
    """
    permission_classes = [IsAdmin]
    
    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="Product analytics",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'top_products': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'product_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'product_name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'total_quantity': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'total_sales': openapi.Schema(type=openapi.TYPE_NUMBER)
                                }
                            )
                        )
                    }
                )
            )
        }
    )
    def get(self, request):
        # Get the top 10 products by quantity sold
        top_products = OrderItem.objects.values(
            'product__id', 'product__name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_sales=Sum('price')
        ).order_by('-total_quantity')[:10]
        
        return Response({
            'top_products': top_products
        })

