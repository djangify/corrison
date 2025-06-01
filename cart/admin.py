# cart/admin.py
from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1
    fields = (
        "product",
        "variant",
        "quantity",
        "unit_price",
        "total_price",
        "is_digital_display",
    )
    readonly_fields = ("unit_price", "total_price", "is_digital_display")

    def is_digital_display(self, obj):
        """Display if cart item is digital"""
        if obj.is_digital:
            return "Digital"
        return "Physical"

    is_digital_display.short_description = "Type"


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "session_key",
        "token_preview",
        "is_active",
        "cart_type_display",
        "created_at",
        "subtotal",
        "total_items",
    )
    list_filter = ("is_active", "has_digital_items", "has_physical_items", "created_at")
    search_fields = ("user__email", "session_key", "token")
    readonly_fields = ("subtotal", "total_items", "cart_type_display", "token_preview")
    inlines = [CartItemInline]

    fieldsets = (
        (None, {"fields": ("user", "session_key", "token_preview", "is_active")}),
        (
            "Cart Type",
            {
                "fields": (
                    "has_digital_items",
                    "has_physical_items",
                    "cart_type_display",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Totals", {"fields": ("subtotal", "total_items")}),
    )

    def subtotal(self, obj):
        return f"${obj.subtotal:.2f}"

    subtotal.admin_order_field = "subtotal"

    def total_items(self, obj):
        return obj.total_items

    total_items.admin_order_field = "total_items"

    def cart_type_display(self, obj):
        """Display cart type with icons"""
        if obj.has_digital_items and obj.has_physical_items:
            return "Mixed Cart"
        elif obj.has_digital_items:
            return "Digital Only"
        elif obj.has_physical_items:
            return "Physical Only"
        return "🛒 Empty"

    cart_type_display.short_description = "Cart Type"

    def token_preview(self, obj):
        """Show preview of JWT token"""
        if obj.token:
            return f"{obj.token[:20]}..." if len(obj.token) > 20 else obj.token
        return "No token"

    token_preview.short_description = "JWT Token"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "cart",
        "product",
        "variant",
        "quantity",
        "unit_price",
        "total_price",
        "is_digital_display",
    )
    list_filter = ("cart__is_active", "product__product_type")
    search_fields = ("cart__user__email", "product__name")
    readonly_fields = ("unit_price", "total_price", "is_digital_display")

    def is_digital_display(self, obj):
        """Display if cart item is digital"""
        if obj.is_digital:
            return "Digital"
        return "Physical"

    is_digital_display.short_description = "Type"
