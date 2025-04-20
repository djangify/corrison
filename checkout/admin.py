from django.contrib import admin
from .models import Address, Order, OrderItem, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'variant', 'product_name', 'variant_name', 'sku', 'price', 'quantity', 'total_price')


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('payment_method', 'transaction_id', 'amount', 'status', 'created_at')


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'city', 'country', 'is_default_shipping', 'is_default_billing')
    list_filter = ('is_default_shipping', 'is_default_billing', 'country')
    search_fields = ('user__email', 'full_name', 'address_line1', 'city', 'postal_code')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'payment_status', 'total', 'created_at')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('order_number', 'user__email', 'guest_email')
    readonly_fields = ('order_number', 'subtotal', 'total')
    fieldsets = (
        (None, {
            'fields': ('order_number', 'user', 'guest_email', 'status', 'payment_status')
        }),
        ('Addresses', {
            'fields': ('shipping_address', 'billing_address')
        }),
        ('Shipping', {
            'fields': ('shipping_method', 'tracking_number')
        }),
        ('Totals', {
            'fields': ('subtotal', 'shipping_cost', 'tax_amount', 'discount_amount', 'total')
        }),
        ('Payment', {
            'fields': ('payment_method', 'payment_id')
        }),
        ('Notes', {
            'fields': ('customer_notes', 'admin_notes')
        }),
    )
    inlines = [OrderItemInline, PaymentInline]
    date_hierarchy = 'created_at'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_name', 'variant_name', 'sku', 'price', 'quantity', 'total_price')
    list_filter = ('order__status',)
    search_fields = ('order__order_number', 'product_name', 'sku')
    readonly_fields = ('total_price',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'payment_method', 'transaction_id', 'amount', 'status', 'created_at')
    list_filter = ('payment_method', 'status', 'created_at')
    search_fields = ('order__order_number', 'transaction_id')
    readonly_fields = ('order', 'payment_method', 'transaction_id', 'amount', 'created_at')
    date_hierarchy = 'created_at'
    