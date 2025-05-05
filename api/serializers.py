from rest_framework import serializers
from products.models import Product
from checkout.models import Address, Order, OrderItem, Payment
from django.contrib.auth import get_user_model

User = get_user_model()

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.StringRelatedField()
    variant = serializers.StringRelatedField()

    class Meta:
        model = OrderItem
        fields = (
            'id', 'order', 'product', 'variant',
            'product_name', 'variant_name', 'sku',
            'price', 'quantity', 'total_price',
        )

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField()
    shipping_address = AddressSerializer(read_only=True)
    billing_address = AddressSerializer(read_only=True)

    class Meta:
        model = Order
        fields = (
            'id', 'user', 'guest_email', 'order_number',
            'status', 'payment_status',
            'shipping_address', 'billing_address',
            'shipping_method', 'tracking_number',
            'subtotal', 'shipping_cost', 'tax_amount',
            'discount_amount', 'total',
            'customer_notes', 'admin_notes',
            'items', 'created_at',
        )

class PaymentSerializer(serializers.ModelSerializer):
    order = serializers.StringRelatedField()

    class Meta:
        model = Payment
        fields = (
            'id', 'order', 'payment_method',
            'transaction_id', 'amount', 'status',
            'payment_data', 'created_at',
        )

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'date_joined')