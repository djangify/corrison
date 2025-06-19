# cart/models.py
from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
from core.models import TimestampedModel
from products.models import Product, ProductVariant

User = get_user_model()


class Cart(models.Model):
    """
    Shopping cart model for digital products.
    Uses Django sessions for identification.
    """

    user = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="carts"
    )
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["session_key", "is_active"]),
            models.Index(fields=["user", "is_active"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.email}"
        return f"Cart {self.id} (Session: {self.session_key[:8]}...)"

    @property
    def subtotal(self):
        """Calculate cart subtotal."""
        total = Decimal("0.00")
        for item in self.items.all():
            total += Decimal(str(item.total_price))
        return total

    @property
    def tax(self):
        """Tax calculation - returns 0 for digital products."""
        return Decimal("0.00")

    @property
    def shipping(self):
        """Shipping cost - returns 0 for digital products."""
        return Decimal("0.00")

    @property
    def total(self):
        """Calculate total amount (for digital products, equals subtotal)."""
        return self.subtotal

    @property
    def total_items(self):
        """Get total number of items in cart."""
        return self.items.count()

    @property
    def total_quantity(self):
        """Get total quantity of all items."""
        return sum(item.quantity for item in self.items.all())

    def clear(self):
        """Clear all items from the cart."""
        self.items.all().delete()

    def merge_with(self, other_cart):
        """
        Merge another cart into this one.
        Used when anonymous user logs in.
        """
        if not other_cart or other_cart.id == self.id:
            return

        for item in other_cart.items.all():
            try:
                # Check if product already exists in this cart
                existing_item = self.items.get(
                    product=item.product, variant=item.variant
                )
                existing_item.quantity += item.quantity
                existing_item.save()
            except CartItem.DoesNotExist:
                # Move item to this cart
                item.cart = self
                item.save()

        # Deactivate the other cart
        other_cart.is_active = False
        other_cart.save()


class CartItem(TimestampedModel):
    """Shopping cart item model for digital products."""

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, null=True, blank=True
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"
        unique_together = ("cart", "product", "variant")
        indexes = [
            models.Index(fields=["cart", "product"]),
        ]

    def __str__(self):
        if self.variant:
            return f"{self.quantity} x {self.product.name} ({self.variant})"
        return f"{self.quantity} x {self.product.name}"

    @property
    def unit_price(self):
        """Get the unit price of the item."""
        if self.variant and self.variant.price:
            return self.variant.price
        return self.product.current_price or self.product.price

    @property
    def total_price(self):
        """Calculate the total price for this item."""
        return Decimal(str(self.unit_price)) * self.quantity

    @property
    def product_name(self):
        """Get product name for serialization."""
        return self.product.name

    @property
    def product_image(self):
        """Get product image URL."""
        if self.product.main_image:
            return self.product.main_image.url
        return None
