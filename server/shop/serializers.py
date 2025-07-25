from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from .models import Product, Order, OrderItem, Sale

class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for product information.
    """
    class Meta:
        model = Product
        fields = ['id', 'sku_code', 'name', 'description', 'price', 'image']
        read_only_fields = ['id']


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating products.
    """
    class Meta:
        model = Product
        fields = ['sku_code', 'name', 'description', 'price', 'image']
    
    def validate_sku_code(self, value):
        """
        Validate that the SKU code is unique.
        """
        instance = self.instance
        if instance is None:  # Creating a new product
            if Product.objects.filter(sku_code=value).exists():
                raise serializers.ValidationError(_("A product with this SKU code already exists."))
        else:  # Updating an existing product
            if Product.objects.exclude(pk=instance.pk).filter(sku_code=value).exists():
                raise serializers.ValidationError(_("A product with this SKU code already exists."))
        return value
    
    def validate_price(self, value):
        """
        Validate that the price is positive.
        """
        if value <= 0:
            raise serializers.ValidationError(_("Price must be greater than zero."))
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for order item information.
    """
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_price', 'quantity', 'price']
        read_only_fields = ['id', 'price', 'product_name', 'product_price']


class OrderItemCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating order items.
    """
    product_id = serializers.PrimaryKeyRelatedField(
        source='product',
        queryset=Product.objects.all()
    )
    
    class Meta:
        model = OrderItem
        fields = ['product_id', 'quantity']
    
    def validate_quantity(self, value):
        """
        Validate that the quantity is positive.
        """
        if value <= 0:
            raise serializers.ValidationError(_("Quantity must be greater than zero."))
        return value


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for order information.
    """
    items = OrderItemSerializer(source='orderitem_set', many=True, read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    total_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['id', 'user', 'user_email', 'status', 'created_at', 'items', 'total_amount']
        read_only_fields = ['id', 'user', 'user_email', 'created_at']
    
    def get_total_amount(self, obj):
        """
        Calculate the total amount of the order.
        """
        return sum(item.price * item.quantity for item in obj.orderitem_set.all())


class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating orders.
    """
    items = OrderItemCreateSerializer(many=True, write_only=True)
    
    class Meta:
        model = Order
        fields = ['status', 'items']
    
    @transaction.atomic
    def create(self, validated_data):
        """
        Create an order with its items.
        """
        items_data = validated_data.pop('items')
        user = self.context['request'].user
        
        # Create the order
        order = Order.objects.create(user=user, **validated_data)
        
        # Create the order items
        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']
            price = product.price  # Use the current product price
            
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=price
            )
        
        # If the order status is 'completed', create a sale record
        if order.status == 'completed':
            total_amount = sum(item.price * item.quantity for item in order.orderitem_set.all())
            Sale.objects.create(order=order, total_amount=total_amount)
        
        return order


class OrderUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating orders.
    """
    class Meta:
        model = Order
        fields = ['status']
    
    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Update an order and create a sale record if the status is changed to 'completed'.
        """
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        
        # Update the order
        instance = super().update(instance, validated_data)
        
        # If the status is changed to 'completed', create a sale record
        if old_status != 'completed' and new_status == 'completed':
            total_amount = sum(item.price * item.quantity for item in instance.orderitem_set.all())
            Sale.objects.create(order=instance, total_amount=total_amount)
        
        return instance


class SaleSerializer(serializers.ModelSerializer):
    """
    Serializer for sale information.
    """
    order_id = serializers.PrimaryKeyRelatedField(source='order', read_only=True)
    user_email = serializers.EmailField(source='order.user.email', read_only=True)
    
    class Meta:
        model = Sale
        fields = ['id', 'order_id', 'user_email', 'total_amount', 'sale_date']
        read_only_fields = ['id', 'order_id', 'user_email', 'total_amount', 'sale_date']

