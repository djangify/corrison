from django.contrib import admin
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
        "stock_qty",
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
        "product_type",
        "category",
        "price",
        "sale_price",
        "is_featured",
        "in_stock",
        "is_active",
    )
    list_filter = ("category", "product_type", "is_featured", "in_stock", "is_active")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("price", "sale_price", "is_featured", "in_stock", "is_active")
    inlines = [ProductImageInline, ProductVariantInline]
    fieldsets = (
        (None, {"fields": ("name", "slug", "category", "description", "product_type")}),
        ("Pricing", {"fields": ("price", "sale_price")}),
        (
            "Physical Product Settings",
            {
                "fields": ("requires_shipping", "weight", "dimensions"),
                "classes": ("collapse",),
                "description": "Settings for physical products only",
            },
        ),
        (
            "Digital Product Settings",
            {
                "fields": ("digital_file", "download_limit", "download_expiry_days"),
                "classes": ("collapse",),
                "description": "Settings for digital downloads only",
            },
        ),
        (
            "Stock & Status",
            {"fields": ("is_active", "is_featured", "in_stock", "stock_qty")},
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
        "stock_qty",
        "is_active",
    )
    list_filter = ("is_active", "product", "product__product_type")
    search_fields = ("sku", "name", "product__name")
    list_editable = ("price_adjustment", "stock_qty", "is_active")
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
                    "stock_qty",
                    "is_active",
                )
            },
        ),
        (
            "Digital Variant Settings",
            {
                "fields": ("digital_file",),
                "classes": ("collapse",),
                "description": "Override digital file for this specific variant",
            },
        ),
        (
            "Attributes",
            {
                "fields": ("attributes",),
                "description": "Product attributes for this variant (e.g., Color: Red, Size: Large)",
            },
        ),
    )
