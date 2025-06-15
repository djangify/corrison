from django.contrib import admin
from django.db import models
from tinymce.widgets import TinyMCE
from .models import (
    Category,
    Product,
    ProductImage,
    Attribute,
    AttributeValue,
    ProductVariant,
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = (
        "name",
        "sku",
        "price_adjustment",
        "digital_file",
        "is_active",
    )


class AttributeValueInline(admin.TabularInline):
    model = AttributeValue
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("is_active",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "price",
        "sale_price",
        "is_featured",
        "is_active",
        "has_digital_file",
    )
    list_filter = ("category", "is_featured", "is_active")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("price", "sale_price", "is_featured", "is_active")
    inlines = [ProductImageInline, ProductVariantInline]
    fieldsets = (
        (None, {"fields": ("name", "slug", "category", "description")}),
        ("Pricing", {"fields": ("price", "sale_price")}),
        (
            "Digital Download Settings",
            {
                "fields": ("digital_file", "download_limit", "download_expiry_days"),
                "description": "Digital product download settings",
            },
        ),
        (
            "Status & Visibility",
            {"fields": ("is_active", "is_featured")},
        ),
        ("Images", {"fields": ("main_image",)}),
        (
            "SEO",
            {
                "fields": ("meta_title", "meta_description", "meta_keywords"),
                "classes": ("collapse",),
            },
        ),
    )

    formfield_overrides = {
        models.TextField: {"widget": TinyMCE(attrs={"cols": 80, "rows": 20})},
    }

    def has_digital_file(self, obj):
        """Display digital file status"""
        if obj.digital_file:
            return "Available"
        return "No File"

    has_digital_file.short_description = "Download"
    has_digital_file.admin_order_field = "digital_file"

    def get_queryset(self, request):
        """Only show digital products by default"""
        qs = super().get_queryset(request)
        # Show all products but default filter to digital
        return qs

    def get_list_filter(self, request):
        """Add product type filter but default to digital"""
        filters = list(super().get_list_filter(request))
        filters.insert(1, "product_type")  # Add after category filter
        return tuple(filters)

    def save_model(self, request, obj, form, change):
        """Auto-set digital product defaults"""
        # Force product_type to digital for new products
        if not change:  # New product
            obj.product_type = "digital"
            obj.requires_shipping = False
            obj.in_stock = True  # Digital products are always "in stock"
            obj.stock_qty = 0  # Not relevant for digital products

        # Always ensure digital product settings
        if obj.product_type == "digital":
            obj.requires_shipping = False
            obj.in_stock = True
            obj.weight = None
            obj.dimensions = ""

        super().save_model(request, obj, form, change)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "image", "is_primary")
    list_filter = ("is_primary",)
    list_editable = ("is_primary",)
    search_fields = ("product__name", "alt_text")


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [AttributeValueInline]


@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ("attribute", "value")
    list_filter = ("attribute",)
    search_fields = ("value",)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "name",
        "sku",
        "price_adjustment",
        "has_digital_file",
        "is_active",
    )
    list_filter = ("is_active", "product")
    search_fields = ("sku", "name", "product__name")
    list_editable = ("price_adjustment", "is_active")
    filter_horizontal = ("attributes",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "product",
                    "name",
                    "sku",
                    "price_adjustment",
                    "is_active",
                )
            },
        ),
        (
            "Digital File",
            {
                "fields": ("digital_file",),
                "description": "Specific digital file for this variant (overrides product default)",
            },
        ),
        (
            "Attributes",
            {
                "fields": ("attributes",),
                "description": "Product attributes for this variant (e.g., Format: PDF, Language: English)",
            },
        ),
    )

    def has_digital_file(self, obj):
        """Display if variant has a digital file"""
        if obj.digital_file:
            return "Variant File"
        elif obj.product.digital_file:
            return "Product File"
        return "No File"

    has_digital_file.short_description = "Digital File"

    def get_queryset(self, request):
        """Only show variants for digital products"""
        qs = super().get_queryset(request)
        return qs.filter(product__product_type="digital")
