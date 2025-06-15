# products/serializers.py
from rest_framework import serializers
from .models import Product, Category, ProductVariant, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "image"]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "alt_text", "is_primary"]


class ProductVariantSerializer(serializers.ModelSerializer):
    effective_digital_file = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "name",
            "sku",
            "price",
            "sale_price",
            "stock_qty",
            "is_active",
            "price_adjustment",
            "digital_file",
            "effective_digital_file",
        ]

    def get_effective_digital_file(self, obj):
        """Return the effective digital file URL for this variant"""
        file = obj.effective_digital_file
        if file:
            return (
                self.context["request"].build_absolute_uri(file.url)
                if hasattr(file, "url")
                else None
            )
        return None


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)

    # Digital product fields
    is_digital = serializers.BooleanField(read_only=True)
    is_downloadable = serializers.BooleanField(read_only=True)
    is_unlimited_download = serializers.BooleanField(read_only=True)
    digital_file_url = serializers.SerializerMethodField()

    # Fixed main_image field
    main_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "category",
            "description",
            "price",
            "sale_price",
            "is_on_sale",
            "current_price",
            "effective_price",
            "main_image",
            "images",
            "variants",
            "is_featured",
            "in_stock",
            "stock_qty",
            # Digital product fields
            "product_type",
            "is_digital",
            "is_downloadable",
            "requires_shipping",
            "digital_file",
            "digital_file_url",
            "download_limit",
            "download_expiry_days",
            "is_unlimited_download",
            # Physical product fields
            "weight",
            "dimensions",
        ]
        read_only_fields = ["id"]  # Explicitly mark id as read-only

    def get_main_image(self, obj):
        """Return main image URL with fallback to primary ProductImage"""
        request = self.context.get(
            "request"
        )  # FIXED: Use .get() instead of direct access

        # First try the main_image field
        if obj.main_image:
            if request:
                return request.build_absolute_uri(obj.main_image.url)
            else:
                # No request context, build absolute URL manually
                return f"https://corrison.corrisonapi.com{obj.main_image.url}"

        # Fallback to primary ProductImage
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            if request:
                return request.build_absolute_uri(primary_image.image.url)
            else:
                return f"https://corrison.corrisonapi.com{primary_image.image.url}"

        # Fallback to first image if no primary
        first_image = obj.images.first()
        if first_image:
            if request:
                return request.build_absolute_uri(first_image.image.url)
            else:
                return f"https://corrison.corrisonapi.com{first_image.image.url}"

        return None

    def get_digital_file_url(self, obj):
        """Return the digital file URL if it exists"""
        if obj.digital_file:
            request = self.context.get(
                "request"
            )  # FIXED: Use .get() instead of direct access
            if request and hasattr(obj.digital_file, "url"):
                return request.build_absolute_uri(obj.digital_file.url)
            elif hasattr(obj.digital_file, "url"):
                # Fallback when no request context
                return f"https://corrison.corrisonapi.com{obj.digital_file.url}"
        return None

    def to_representation(self, instance):
        """Convert price fields to floats"""
        data = super().to_representation(instance)

        # Convert price fields to floats
        if "price" in data and data["price"] is not None:
            try:
                data["price"] = float(data["price"])
            except (ValueError, TypeError):
                data["price"] = 0.0

        if "sale_price" in data and data["sale_price"] is not None:
            try:
                data["sale_price"] = float(data["sale_price"])
            except (ValueError, TypeError):
                data["sale_price"] = None

        if "current_price" in data and data["current_price"] is not None:
            try:
                data["current_price"] = float(data["current_price"])
            except (ValueError, TypeError):
                data["current_price"] = 0.0

        if "effective_price" in data and data["effective_price"] is not None:
            try:
                data["effective_price"] = float(data["effective_price"])
            except (ValueError, TypeError):
                data["effective_price"] = 0.0

        return data
