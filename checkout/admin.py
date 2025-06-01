from django.contrib import admin
from .models import Order, OrderItem, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        "product",
        "variant",
        "product_name",
        "variant_name",
        "sku",
        "price",
        "quantity",
        "total_price",
        "is_digital",
        "download_token",
        "download_count",
        "max_downloads",
    )
    fields = (
        "product",
        "variant",
        "product_name",
        "variant_name",
        "sku",
        "price",
        "quantity",
        "total_price",
        "is_digital",
        "download_token",
        "download_count",
        "max_downloads",
    )


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = (
        "payment_method",
        "transaction_id",
        "amount",
        "status",
        "created_at",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "user",
        "status",
        "payment_status",
        "has_digital_items",
        "has_physical_items",
        "total",
        "created_at",
    )
    list_filter = (
        "status",
        "payment_status",
        "has_digital_items",
        "has_physical_items",
        "created_at",
    )
    search_fields = ("order_number", "user__email", "guest_email")
    readonly_fields = ("order_number", "subtotal", "total")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "order_number",
                    "user",
                    "guest_email",
                    "status",
                    "payment_status",
                )
            },
        ),
        (
            "Order Type",
            {
                "fields": (
                    "has_digital_items",
                    "has_physical_items",
                    "digital_delivery_email",
                )
            },
        ),
        (
            "Shipping Info",
            {
                "fields": ("shipping_method", "tracking_number"),
                "description": "Only applies to orders with physical items",
            },
        ),
        (
            "Totals",
            {
                "fields": (
                    "subtotal",
                    "shipping_cost",
                    "tax_amount",
                    "discount_amount",
                    "total",
                )
            },
        ),
        ("Payment", {"fields": ("payment_method", "payment_id")}),
        ("Notes", {"fields": ("customer_notes", "admin_notes")}),
    )
    inlines = [OrderItemInline, PaymentInline]
    date_hierarchy = "created_at"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "product_name",
        "variant_name",
        "sku",
        "price",
        "quantity",
        "total_price",
        "is_digital",
        "download_count",
    )
    list_filter = ("order__status", "is_digital")
    search_fields = ("order__order_number", "product_name", "sku")
    readonly_fields = ("total_price",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "order",
                    "product",
                    "variant",
                    "product_name",
                    "variant_name",
                    "sku",
                    "price",
                    "quantity",
                    "total_price",
                )
            },
        ),
        (
            "Digital Product Settings",
            {
                "fields": (
                    "is_digital",
                    "download_token",
                    "download_expires_at",
                    "download_count",
                    "max_downloads",
                ),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "payment_method",
        "transaction_id",
        "amount",
        "status",
        "created_at",
    )
    list_filter = ("payment_method", "status", "created_at")
    search_fields = ("order__order_number", "transaction_id")
    readonly_fields = (
        "order",
        "payment_method",
        "transaction_id",
        "amount",
        "created_at",
    )
    date_hierarchy = "created_at"
