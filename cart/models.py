# cart/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from core.models import TimestampedModel, UUIDModel
from products.models import Product, ProductVariant

User = get_user_model()

class Cart(UUIDModel, TimestampedModel):
    """
    Shopping cart model.
    """
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='carts',
        null=True, blank=True
    )
    session_key = models.CharField(max_length=255, null=True, blank=True)
    token = models.CharField(max_length=500, null=True, blank=True, db_index=True)  # New field for JWT token
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
            models.Index(fields=['token']),  # New index for token lookups
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        if self.user:
            return f"Cart for {self.user.email}"
        return f"Cart {self.id}"
    
    @property
    def subtotal(self):
        """
        Calculate cart subtotal.
        """
        return sum(item.total_price for item in self.items.all())

    @property
    def total_items(self):
        """
        Get total number of items in cart.
        """
        return self.items.count()
    
    def clear(self):
        """
        Clear all items from the cart.
        """
        self.items.all().delete()

    @classmethod
    def get_or_create_cart(cls, user=None, token=None):
        """
        Get or create a cart based on user or token
        """
        cart = None
        
        if user and user.is_authenticated:
            # Try to get user's active cart
            cart = cls.objects.filter(user=user, is_active=True).first()
        elif token:
            # Try to get cart by token
            cart = cls.objects.filter(token=token, is_active=True).first()
        
        # Create new cart if needed
        if not cart:
            cart = cls.objects.create(
                user=user if user and user.is_authenticated else None,
                token=token
            )
        
        return cart


class CartItem(UUIDModel, TimestampedModel):
    """
    Shopping cart item model.
    """
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE
    )
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE,
        null=True, blank=True
    )
    quantity = models.PositiveIntegerField(default=1)
    
    class Meta:
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'
        unique_together = ('cart', 'product', 'variant')
        indexes = [
            models.Index(fields=['cart']),
            models.Index(fields=['product']),
        ]
    
    def __str__(self):
        if self.variant:
            return f"{self.quantity} x {self.product.name} ({self.variant})"
        return f"{self.quantity} x {self.product.name}"
    
    @property
    def unit_price(self):
        """
        Get the unit price of the item.
        """
        if self.variant:
            return self.variant.price
        return self.product.current_price

    @property
    def total_price(self):
        """
        Calculate the total price for this item.
        """
        return self.unit_price * self.quantity