from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Product, Order, OrderItem, Sale
from django.db import transaction
from decimal import Decimal

class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for Product model.
    """
    class Meta:
        model = Product
        fields = ['id', 'sku_code', 'name', 'description', 'price', 'image', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for OrderItem model.
    """
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_price', 'quantity', 'price', 'created_at', 'updated_at']
        read_only_fields = ['id', 'price', 'created_at', 'updated_at']

class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for Order model.
    """
    items = OrderItemSerializer(source='orderitem_set', many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'user', 'user_email', 'status', 'items', 'total_amount', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_total_amount(self, obj):
        """
        Calculate the total amount of the order.
        """
        return sum(item.price * item.quantity for item in obj.orderitem_set.all())

class OrderCreateSerializer(serializers.Serializer):
    """
    Serializer for creating an order.
    """
    status = serializers.ChoiceField(choices=[
        ('pending', 'Pending'), 
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='pending')
    
    items = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField(),
            allow_empty=False
        ),
        min_length=1
    )
    
    def validate_items(self, items):
        """
        Validate the items in the order.
        """
        validated_items = []
        
        for item in items:
            if 'product_id' not in item or 'quantity' not in item:
                raise serializers.ValidationError(_("Each item must have 'product_id' and 'quantity'."))
            
            product_id = item['product_id']
            quantity = item['quantity']
            
            # Validate quantity
            if quantity <= 0:
                raise serializers.ValidationError(_("Quantity must be greater than 0."))
            
            # Validate product exists
            try:
                product = Product.objects.get(id=product_id)
                validated_items.append({
                    'product': product,
                    'quantity': quantity
                })
            except Product.DoesNotExist:
                raise serializers.ValidationError(_("Product with id '{}' does not exist.").format(product_id))
        
        return validated_items
    
    @transaction.atomic
    def create(self, validated_data):
        """
        Create an order with the given items.
        """
        user = self.context['request'].user
        status = validated_data.get('status', 'pending')
        items = validated_data.get('items', [])
        
        # Create order
        order = Order.objects.create(
            user=user,
            status=status
        )
        
        # Create order items
        for item in items:
            product = item['product']
            quantity = item['quantity']
            
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price
            )
        
        # If order is completed, create a sale record
        if status == 'completed':
            total_amount = sum(item['product'].price * item['quantity'] for item in items)
            Sale.objects.create(
                order=order,
                total_amount=total_amount
            )
        
        return order

class SaleSerializer(serializers.ModelSerializer):
    """
    Serializer for Sale model.
    """
    order_id = serializers.UUIDField(source='order.id', read_only=True)
    user_email = serializers.EmailField(source='order.user.email', read_only=True)
    
    class Meta:
        model = Sale
        fields = ['id', 'order_id', 'user_email', 'total_amount', 'sale_date', 'created_at', 'updated_at']
        read_only_fields = ['id', 'order_id', 'user_email', 'sale_date', 'created_at', 'updated_at']

