# cart/serializers.py
from rest_framework import serializers
from .models import Cart, CartItem
from products.serializers import ProductSerializer, ProductVariantSerializer


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    unit_price = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
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

    def get_unit_price(self, obj):
        """Return unit price as float"""
        try:
            return float(obj.unit_price)
        except (ValueError, TypeError, AttributeError):
            return 0.0

    def get_total_price(self, obj):
        """Return total price as float"""
        try:
            return float(obj.total_price)
        except (ValueError, TypeError, AttributeError):
            return 0.0

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1")
        return value


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()
    tax = serializers.SerializerMethodField()
    shipping = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    total_items = serializers.IntegerField(read_only=True)
    token = serializers.CharField(read_only=True)

    # Simplified digital-only flags
    has_digital_items = serializers.SerializerMethodField()
    has_physical_items = serializers.SerializerMethodField()
    requires_shipping = serializers.SerializerMethodField()
    is_digital_only = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            "id",
            "items",
            "subtotal",
            "tax",
            "shipping",
            "total",
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

    def get_subtotal(self, obj):
        """Return subtotal as a float"""
        return float(obj.subtotal)

    def get_tax(self, obj):
        """Return tax as a float"""
        return float(obj.tax)

    def get_shipping(self, obj):
        """Return shipping as a float"""
        return float(obj.shipping)

    def get_total(self, obj):
        """Return total as a float"""
        return float(obj.total)

    def get_has_digital_items(self, obj):
        """Always True for digital-only system"""
        return obj.items.exists()

    def get_has_physical_items(self, obj):
        """Always False for digital-only system"""
        return False

    def get_requires_shipping(self, obj):
        """Always False for digital-only system"""
        return False

    def get_is_digital_only(self, obj):
        """Always True for digital-only system"""
        return obj.items.exists()
