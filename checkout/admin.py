from django.contrib import admin
from .models import Order, OrderItem, Payment, OrderSettings
from django.db import models
from tinymce.widgets import TinyMCE as RichTextEditorWidget


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
        "download_status",
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
        "download_expires_at",
        "download_count",
        "max_downloads",
        "download_status",
    )

    def download_status(self, obj):
        """Display download status"""
        if not obj.is_digital:
            return "N/A"
        if obj.can_download:
            remaining = (
                obj.max_downloads - obj.download_count if obj.max_downloads > 0 else "∞"
            )
            return f"✅ Active ({remaining} left)"
        return "❌ Expired/Limit reached"

    download_status.short_description = "Download Status"


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
        "order_type_display",
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
    readonly_fields = ("order_number", "subtotal", "total", "order_type_display")
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
                    "order_type_display",
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

    def order_type_display(self, obj):
        """Display order type with icons"""
        if obj.has_digital_items and obj.has_physical_items:
            return "🔄 Mixed Order"
        elif obj.has_digital_items:
            return "📱 Digital Only"
        elif obj.has_physical_items:
            return "📦 Physical Only"
        return "🛒 Empty Order"

    order_type_display.short_description = "Order Type"


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
        "item_type_display",
        "download_status_display",
    )
    list_filter = ("order__status", "is_digital", "order__has_digital_items")
    search_fields = ("order__order_number", "product_name", "sku", "download_token")
    readonly_fields = ("total_price", "item_type_display", "download_status_display")
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
                    "item_type_display",
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
                    "download_status_display",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def item_type_display(self, obj):
        """Display item type"""
        if obj.is_digital:
            return "📱 Digital Download"
        return "📦 Physical Item"

    item_type_display.short_description = "Item Type"

    def download_status_display(self, obj):
        """Display download status for digital items"""
        if not obj.is_digital:
            return "N/A - Physical Item"

        if not obj.download_token:
            return "❌ No download token"

        if obj.can_download:
            if obj.max_downloads > 0:
                remaining = obj.max_downloads - obj.download_count
                return f"✅ Active ({obj.download_count}/{obj.max_downloads} used, {remaining} left)"
            else:
                return f"✅ Active (Unlimited downloads, {obj.download_count} used)"

        # Check why it can't be downloaded
        if obj.download_expires_at:
            from django.utils import timezone

            if timezone.now() > obj.download_expires_at:
                return "❌ Expired"

        if obj.max_downloads > 0 and obj.download_count >= obj.max_downloads:
            return "❌ Download limit reached"

        return "❌ Cannot download"

    download_status_display.short_description = "Download Status"


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


@admin.register(OrderSettings)
class OrderSettingsAdmin(admin.ModelAdmin):
    """
    Admin for order page settings - singleton model
    """

    def has_add_permission(self, request):
        """Only allow adding if no instance exists"""
        return not OrderSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Don't allow deletion of settings"""
        return False

    def changelist_view(self, request, extra_context=None):
        """Redirect to the single instance edit page"""
        try:
            settings = OrderSettings.get_settings()
            return self.changeform_view(request, str(settings.pk))
        except Exception:
            return super().changelist_view(request, extra_context)

    fieldsets = (
        (
            "Page Content",
            {
                "fields": ("page_title", "page_subtitle", "page_description"),
                "description": "Main content for the order history page header",
            },
        ),
    )

    formfield_overrides = {
        models.TextField: {
            "widget": RichTextEditorWidget(attrs={"cols": 80, "rows": 10})
        },
    }
