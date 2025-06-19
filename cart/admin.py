# cart/admin.py
from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = (
        "product",
        "variant",
        "quantity",
        "unit_price",
        "total_price",
    )
    readonly_fields = ("unit_price", "total_price")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "session_key",
        "is_active",
        "total_items",
        "subtotal_display",
        "total_display",
        "created_at",
    )
    list_filter = ("is_active", "created_at", "updated_at")
    search_fields = ("user__email", "session_key")
    readonly_fields = (
        "subtotal_display",
        "total_display",
        "total_items",
        "created_at",
        "updated_at",
    )
    inlines = [CartItemInline]

    fieldsets = (
        (None, {"fields": ("user", "session_key", "is_active")}),
        ("Totals", {"fields": ("total_items", "subtotal_display", "total_display")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def subtotal_display(self, obj):
        return f"${obj.subtotal:.2f}"

    subtotal_display.short_description = "Subtotal"
    subtotal_display.admin_order_field = "subtotal"

    def total_display(self, obj):
        return f"${obj.total:.2f}"

    total_display.short_description = "Total"

    def total_items(self, obj):
        return obj.total_items

    total_items.short_description = "Items"
    total_items.admin_order_field = "total_items"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "cart",
        "product",
        "variant",
        "quantity",
        "unit_price_display",
        "total_price_display",
    )
    list_filter = ("cart__is_active", "created_at")
    search_fields = ("cart__user__email", "product__name")
    readonly_fields = ("unit_price", "total_price", "created_at", "updated_at")

    def unit_price_display(self, obj):
        return f"${obj.unit_price:.2f}"

    unit_price_display.short_description = "Unit Price"

    def total_price_display(self, obj):
        return f"${obj.total_price:.2f}"

    total_price_display.short_description = "Total"
