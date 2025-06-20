# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import WishlistItem, Profile
from products.serializers import ProductSerializer
from products.models import Product


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = WishlistItem
        fields = ["id", "user", "product", "product_id", "created_at"]
        read_only_fields = ["user", "created_at"]

    def create(self, validated_data):
        # Get the product_id from validated data
        product_id = validated_data.pop("product_id", None)

        # If product_id is provided in the data, use it
        if not product_id and "product" in self.initial_data:
            product_id = self.initial_data["product"]

        if not product_id:
            raise serializers.ValidationError("Product ID is required")

        # Get the product
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or not active")

        # Get the user from the request context
        user = self.context["request"].user

        # Check if item already exists in wishlist
        if WishlistItem.objects.filter(user=user, product=product).exists():
            raise serializers.ValidationError("Product already in wishlist")

        # Create the wishlist item
        return WishlistItem.objects.create(user=user, product=product)


class WishlistItemCreateSerializer(serializers.Serializer):
    """Simplified serializer for creating wishlist items"""

    product = serializers.UUIDField()

    def validate_product(self, value):
        try:
            Product.objects.get(id=value, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or not active")
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile data"""

    class Meta:
        model = Profile
        fields = [
            "phone",
            "birth_date",
            "email_marketing",
            "receive_order_updates",
            "email_verified",
        ]
        read_only_fields = ["email_verified"]


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data with profile"""

    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "profile",
            "date_joined",
            "is_staff",
            "is_superuser",
        ]
        read_only_fields = ["id", "date_joined"]


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
        ]
        extra_kwargs = {
            "email": {"required": True},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "A user with this username already exists."
            )
        return value

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""

    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError("Invalid username or password.")
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled.")

            attrs["user"] = user
            return attrs
        else:
            raise serializers.ValidationError("Must include username and password.")


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for email verification"""

    token = serializers.CharField()

    def validate_token(self, value):
        try:
            profile = Profile.objects.get(email_verification_token=value)
            if profile.email_verified:
                raise serializers.ValidationError("Email is already verified.")
            return value
        except Profile.DoesNotExist:
            raise serializers.ValidationError("Invalid verification token.")


class ResendVerificationSerializer(serializers.Serializer):
    """Serializer for resending verification email"""

    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            if user.profile.email_verified:
                raise serializers.ValidationError("Email is already verified.")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address.")


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""

    current_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    confirm_password = serializers.CharField()

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"new_password": "Password fields didn't match."}
            )
        return attrs

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""

    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    email = serializers.EmailField(source="user.email")

    class Meta:
        model = Profile
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "birth_date",
            "email_marketing",
            "receive_order_updates",
        ]

    def validate_email(self, value):
        user = self.context["request"].user
        if User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})

        # Update user fields
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        instance.user.save()

        # Update profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance
