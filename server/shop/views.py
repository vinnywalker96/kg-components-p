from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.db import transaction
from django.db.models import Sum, Count, F, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import Product, Order, OrderItem, Sale
from .serializers import (
    ProductSerializer,
    OrderSerializer,
    OrderCreateSerializer,
    SaleSerializer
)
from .permissions import IsAdminOrReadOnly, IsOwnerOrAdmin

class ProductListView(generics.ListAPIView):
    """
    API view for listing products.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'sku_code']
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['-created_at']

class ProductDetailView(generics.RetrieveAPIView):
    """
    API view for retrieving product details.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'

class ProductCreateView(generics.CreateAPIView):
    """
    API view for creating a product.
    """
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]

class ProductUpdateView(generics.UpdateAPIView):
    """
    API view for updating a product.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'id'

class ProductDeleteView(generics.DestroyAPIView):
    """
    API view for deleting a product.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'id'

class OrderListView(generics.ListAPIView):
    """
    API view for listing orders.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Return orders for the current user, or all orders for admin users.
        """
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=user)

class OrderDetailView(generics.RetrieveAPIView):
    """
    API view for retrieving order details.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    lookup_field = 'id'
    
    def get_queryset(self):
        """
        Return orders for the current user, or all orders for admin users.
        """
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=user)

class OrderCreateView(generics.CreateAPIView):
    """
    API view for creating an order.
    """
    serializer_class = OrderCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_context(self):
        """
        Add request to serializer context.
        """
        context = super().get_serializer_context()
        context.update({
            'request': self.request
        })
        return context

class OrderUpdateView(generics.UpdateAPIView):
    """
    API view for updating an order.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    lookup_field = 'id'
    
    def get_queryset(self):
        """
        Return orders for the current user, or all orders for admin users.
        """
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=user)
    
    @transaction.atomic
    def perform_update(self, serializer):
        """
        Update the order and create a sale record if the status is changed to 'completed'.
        """
        instance = self.get_object()
        old_status = instance.status
        new_status = serializer.validated_data.get('status', old_status)
        
        # Update the order
        order = serializer.save()
        
        # If status is changed to 'completed', create a sale record
        if old_status != 'completed' and new_status == 'completed':
            # Calculate total amount
            total_amount = sum(item.price * item.quantity for item in order.orderitem_set.all())
            
            # Create sale record
            Sale.objects.create(
                order=order,
                total_amount=total_amount
            )

class SaleListView(generics.ListAPIView):
    """
    API view for listing sales.
    """
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['sale_date', 'total_amount']
    ordering = ['-sale_date']

@api_view(['GET'])
@permission_classes([IsAdminUser])
def sales_analytics(request):
    """
    API view for sales analytics.
    """
    # Get query parameters
    period = request.query_params.get('period', 'all')
    
    # Filter sales based on period
    if period == 'today':
        sales = Sale.objects.filter(sale_date__date=timezone.now().date())
    elif period == 'week':
        sales = Sale.objects.filter(sale_date__gte=timezone.now() - timedelta(days=7))
    elif period == 'month':
        sales = Sale.objects.filter(sale_date__gte=timezone.now() - timedelta(days=30))
    else:
        sales = Sale.objects.all()
    
    # Calculate analytics
    total_sales = sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    total_orders = sales.count()
    
    # Get sales by day
    sales_by_day = sales.extra(
        select={'day': "DATE(sale_date)"}
    ).values('day').annotate(
        total=Sum('total_amount'),
        count=Count('id')
    ).order_by('day')
    
    return Response({
        'total_sales': total_sales,
        'total_orders': total_orders,
        'sales_by_day': sales_by_day
    })

@api_view(['GET'])
@permission_classes([IsAdminUser])
def product_analytics(request):
    """
    API view for product analytics.
    """
    # Get top selling products
    top_products = OrderItem.objects.values(
        'product__id', 'product__name', 'product__sku_code'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_sales=Sum(F('quantity') * F('price'))
    ).order_by('-total_quantity')[:10]
    
    # Get products with no sales
    all_product_ids = set(Product.objects.values_list('id', flat=True))
    sold_product_ids = set(OrderItem.objects.values_list('product_id', flat=True).distinct())
    unsold_product_ids = all_product_ids - sold_product_ids
    
    unsold_products = Product.objects.filter(id__in=unsold_product_ids).values(
        'id', 'name', 'sku_code'
    )
    
    return Response({
        'top_products': top_products,
        'unsold_products': unsold_products
    })

