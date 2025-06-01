# cart/serializers.py
from rest_framework import serializers
from .models import Cart, CartItem
from products.serializers import ProductSerializer, ProductVariantSerializer


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    unit_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    total_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    is_digital = serializers.BooleanField(read_only=True)

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",
            "variant",
            "quantity",
            "unit_price",
            "total_price",
            "is_digital",
        ]
        read_only_fields = ["id", "unit_price", "total_price", "is_digital"]

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1")
        return value


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    token = serializers.CharField(read_only=True)

    # Digital cart support
    has_digital_items = serializers.BooleanField(read_only=True)
    has_physical_items = serializers.BooleanField(read_only=True)
    requires_shipping = serializers.BooleanField(read_only=True)
    is_digital_only = serializers.BooleanField(read_only=True)

    class Meta:
        model = Cart
        fields = [
            "id",
            "items",
            "subtotal",
            "total_items",
            "created_at",
            "token",
            "has_digital_items",
            "has_physical_items",
            "requires_shipping",
            "is_digital_only",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "token",
            "has_digital_items",
            "has_physical_items",
            "requires_shipping",
            "is_digital_only",
        ]
