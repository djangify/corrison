from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('product', 'variant', 'unit_price', 'total_price')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_id', 'is_active', 'created_at', 'item_count', 'subtotal')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__email', 'session_id')
    readonly_fields = ('session_id', 'subtotal', 'item_count')
    inlines = [CartItemInline]
    date_hierarchy = 'created_at'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'product', 'variant', 'quantity', 'unit_price', 'total_price')
    list_filter = ('cart__is_active',)
    search_fields = ('cart__user__email', 'product__name')
    readonly_fields = ('unit_price', 'total_price')
    