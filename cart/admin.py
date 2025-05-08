# cart/admin.py
from django.contrib import admin
from .models import Cart, CartItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1
    fields = ('product', 'variant', 'quantity', 'unit_price', 'total_price')
    readonly_fields = ('unit_price', 'total_price')

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_key', 'is_active', 'created_at', 'subtotal', 'total_items')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__email', 'session_key')
    readonly_fields = ('subtotal', 'total_items')
    inlines = [CartItemInline]
    
    def subtotal(self, obj):
        return sum(item.total_price for item in obj.items.all())
    
    def total_items(self, obj):
        return obj.items.count()

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'product', 'variant', 'quantity', 'unit_price', 'total_price')
    list_filter = ('cart__is_active',)
    search_fields = ('cart__user__email', 'product__name')
    readonly_fields = ('unit_price', 'total_price')