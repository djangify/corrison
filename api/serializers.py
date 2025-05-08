from rest_framework import serializers, status, viewsets
from checkout.models import Address, Order, OrderItem, Payment
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


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

class UserCreateUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,  # allow updates without changing password
        validators=[validate_password],
        style={'input_type': 'password'},
    )
    password2 = serializers.CharField(
        write_only=True,
        required=False,
        style={'input_type': 'password'},
        label="Confirm password",
    )

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'password2')
        extra_kwargs = {
            'email': {'required': True},
        }

    def validate(self, attrs):
        pw = attrs.get('password')
        pw2 = attrs.get('password2')
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
        validated_data.pop('password2', None)
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data, password=password)
        return user

    def update(self, instance, validated_data):
        # Pop out password fields if present
        password = validated_data.pop('password', None)
        validated_data.pop('password2', None)

        # Update other fields normally
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # If user supplied a new password, hash & set it
        if password:
            instance.set_password(password)

        instance.save()
        return instance
