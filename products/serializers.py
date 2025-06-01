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

    def get_digital_file_url(self, obj):
        """Return the digital file URL if it exists"""
        if obj.digital_file:
            return (
                self.context["request"].build_absolute_uri(obj.digital_file.url)
                if hasattr(obj.digital_file, "url")
                else None
            )
        return None
