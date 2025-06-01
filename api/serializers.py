from rest_framework import serializers
from checkout.models import Order, OrderItem, Payment
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from products.models import Category

User = get_user_model()


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.StringRelatedField()
    variant = serializers.StringRelatedField()

    # Digital download fields
    can_download = serializers.BooleanField(read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = (
            "id",
            "order",
            "product",
            "variant",
            "product_name",
            "variant_name",
            "sku",
            "price",
            "quantity",
            "total_price",
            # Digital download fields
            "is_digital",
            "download_token",
            "download_expires_at",
            "download_count",
            "max_downloads",
            "can_download",
            "download_url",
        )

    def get_download_url(self, obj):
        """Generate download URL for digital items"""
        if obj.is_digital and obj.download_token and obj.can_download:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(f"/downloads/{obj.download_token}/")
        return None


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField()

    # Digital order fields
    delivery_email = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            "id",
            "user",
            "guest_email",
            "order_number",
            "status",
            "payment_status",
            "shipping_method",
            "tracking_number",
            "subtotal",
            "shipping_cost",
            "tax_amount",
            "discount_amount",
            "total",
            "customer_notes",
            "admin_notes",
            "items",
            "created_at",
            # Digital order fields
            "has_digital_items",
            "has_physical_items",
            "digital_delivery_email",
            "is_digital_only",
            "requires_shipping",
            "delivery_email",
        )

    def get_delivery_email(self, obj):
        """Get the delivery email for digital products"""
        return obj.get_delivery_email()


class PaymentSerializer(serializers.ModelSerializer):
    order = serializers.StringRelatedField()

    class Meta:
        model = Payment
        fields = (
            "id",
            "order",
            "payment_method",
            "transaction_id",
            "amount",
            "status",
            "payment_data",
            "created_at",
        )


class UserCreateUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,  # allow updates without changing password
        validators=[validate_password],
        style={"input_type": "password"},
    )
    password2 = serializers.CharField(
        write_only=True,
        required=False,
        style={"input_type": "password"},
        label="Confirm password",
    )

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "password2")
        extra_kwargs = {
            "email": {"required": True},
        }

    def validate(self, attrs):
        pw = attrs.get("password")
        pw2 = attrs.get("password2")
        # On create, both are required; on update, only if one is present
        if self.instance is None:
            # creation: must supply both
            if not pw or not pw2:
                raise serializers.ValidationError(
                    {"password": "Both password fields are required."}
                )
        if pw or pw2:
            # if either present, enforce match
            if pw != pw2:
                raise serializers.ValidationError({"password": "Passwords must match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2", None)
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data, password=password)
        return user

    def update(self, instance, validated_data):
        # Pop out password fields if present
        password = validated_data.pop("password", None)
        validated_data.pop("password2", None)

        # Update other fields normally
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # If user supplied a new password, hash & set it
        if password:
            instance.set_password(password)

        instance.save()
        return instance


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description", "image")
