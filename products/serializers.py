from rest_framework import serializers
from .models import Product, Category, ProductVariant, ProductImage
from core.mixins import MediaURLMixin  # ADD THIS LINE


class CategorySerializer(
    MediaURLMixin, serializers.ModelSerializer
):  # ADD MediaURLMixin
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "image"]


class ProductImageSerializer(
    MediaURLMixin, serializers.ModelSerializer
):  # ADD MediaURLMixin
    class Meta:
        model = ProductImage
        fields = ["id", "image", "alt_text", "is_primary"]


class ProductVariantSerializer(
    MediaURLMixin, serializers.ModelSerializer
):  # ADD MediaURLMixin
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


class ProductSerializer(
    MediaURLMixin, serializers.ModelSerializer
):  # ADD MediaURLMixin
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
        request = self.context.get("request")

        # First try the main_image field
        if obj.main_image:
            return (
                request.build_absolute_uri(obj.main_image.url)
                if request
                else obj.main_image.url
            )

        # Fallback to primary ProductImage
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return (
                request.build_absolute_uri(primary_image.image.url)
                if request
                else primary_image.image.url
            )

        # Fallback to first image if no primary
        first_image = obj.images.first()
        if first_image:
            return (
                request.build_absolute_uri(first_image.image.url)
                if request
                else first_image.image.url
            )

        return None

    def get_digital_file_url(self, obj):
        """Return the digital file URL if it exists"""
        if obj.digital_file:
            return (
                self.context["request"].build_absolute_uri(obj.digital_file.url)
                if hasattr(obj.digital_file, "url")
                else None
            )
        return None
