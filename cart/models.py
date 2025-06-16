# cart/models.py
from django.db import models
from django.contrib.auth import get_user_model
from core.models import TimestampedModel
from products.models import Product, ProductVariant

User = get_user_model()


class Cart(TimestampedModel):
    """
    Shopping cart model.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="carts", null=True, blank=True
    )
    session_key = models.CharField(max_length=255, null=True, blank=True)
    token = models.CharField(
        max_length=500, null=True, blank=True, db_index=True
    )  # JWT token
    is_active = models.BooleanField(default=True)

    # Digital order support
    has_digital_items = models.BooleanField(default=False)
    has_physical_items = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Cart"
        verbose_name_plural = "Carts"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["session_key"]),
            models.Index(fields=["token"]),
            models.Index(fields=["is_active"]),
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
        from decimal import Decimal

        return sum(item.total_price for item in self.items.all()) or Decimal("0.00")

    @property
    def tax(self):
        """
        Calculate tax amount. For digital products, this is typically 0.
        Can be overridden later for physical products or specific tax rules.
        """
        from decimal import Decimal

        return Decimal("0.00")

    @property
    def shipping(self):
        """
        Calculate shipping cost. For digital products, this is always 0.
        """
        from decimal import Decimal

        return Decimal("0.00")

    @property
    def total(self):
        """
        Calculate total amount (subtotal + tax + shipping).
        For digital-only products, this equals subtotal.
        """
        return self.subtotal + self.tax + self.shipping

    @property
    def total_items(self):
        """
        Get total number of items in cart.
        """
        return self.items.count()

    @property
    def requires_shipping(self):
        """
        Returns True if cart contains physical items that need shipping.
        """
        return self.has_physical_items

    @property
    def is_digital_only(self):
        """
        Returns True if cart contains only digital items.
        """
        return self.has_digital_items and not self.has_physical_items

    def update_item_types(self):
        """
        Update has_digital_items and has_physical_items based on cart contents.
        """
        items = self.items.select_related("product").all()

        self.has_digital_items = any(item.product.is_digital for item in items)
        self.has_physical_items = any(not item.product.is_digital for item in items)

        self.save(update_fields=["has_digital_items", "has_physical_items"])

    def clear(self):
        """
        Clear all items from the cart.
        """
        self.items.all().delete()
        self.has_digital_items = False
        self.has_physical_items = False
        self.save(update_fields=["has_digital_items", "has_physical_items"])

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
                user=user if user and user.is_authenticated else None, token=token
            )

        return cart


class CartItem(TimestampedModel):
    """
    Shopping cart item model.
    """

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
            models.Index(fields=["cart"]),
            models.Index(fields=["product"]),
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

    @property
    def is_digital(self):
        """
        Returns True if this cart item is for a digital product.
        """
        return self.product.is_digital

    def save(self, *args, **kwargs):
        """
        Override save to update cart item types when cart item is saved.
        """
        super().save(*args, **kwargs)
        # Update cart's digital/physical item flags
        self.cart.update_item_types()

    def delete(self, *args, **kwargs):
        """
        Override delete to update cart item types when cart item is deleted.
        """
        cart = self.cart
        super().delete(*args, **kwargs)
        # Update cart's digital/physical item flags
        cart.update_item_types()
