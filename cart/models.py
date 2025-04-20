from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from core.models import TimestampedModel, UUIDModel
from products.models import Product, ProductVariant

User = get_user_model()


class Cart(UUIDModel, TimestampedModel):
    """
    Shopping cart model to store cart information.
    """
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, 
        blank=True, null=True, 
        related_name='carts'
    )
    session_id = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    # Coupon and additional fields can be added here
    
    class Meta:
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_id']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        if self.user:
            return f"Cart for {self.user.email}"
        return f"Cart {self.id}"
    
    @property
    def subtotal(self):
        """
        Calculate the subtotal of all items in the cart.
        """
        return sum(item.total_price for item in self.items.all())
    
    @property
    def item_count(self):
        """
        Return the total number of items in the cart.
        """
        return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0
    
    def add_item(self, product, quantity=1, variant=None):
        """
        Add an item to the cart.
        """
        if variant:
            cart_item, created = self.items.get_or_create(
                product=product,
                variant=variant,
                defaults={'quantity': quantity}
            )
        else:
            cart_item, created = self.items.get_or_create(
                product=product,
                variant=None,
                defaults={'quantity': quantity}
            )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
            
        return cart_item
    
    def update_item(self, item_id, quantity):
        """
        Update the quantity of an item in the cart.
        """
        try:
            item = self.items.get(id=item_id)
            if quantity > 0:
                item.quantity = quantity
                item.save()
            else:
                item.delete()
            return True
        except CartItem.DoesNotExist:
            return False
    
    def remove_item(self, item_id):
        """
        Remove an item from the cart.
        """
        try:
            item = self.items.get(id=item_id)
            item.delete()
            return True
        except CartItem.DoesNotExist:
            return False
    
    def clear(self):
        """
        Remove all items from the cart.
        """
        self.items.all().delete()
        
    @classmethod
    def get_or_create_cart(cls, request):
        """
        Get or create a cart for the current user or session.
        """
        user = request.user if request.user.is_authenticated else None
        session_id = request.session.session_key
        
        # Create session key if it doesn't exist
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        
        # Try to get an existing active cart
        if user:
            # For logged in users, try to get their cart
            cart = cls.objects.filter(user=user, is_active=True).first()
            if cart:
                return cart
                
            # Also check for a session cart that might need to be associated
            session_cart = cls.objects.filter(session_id=session_id, is_active=True).first()
            if session_cart:
                # Associate the session cart with the user
                session_cart.user = user
                session_cart.save()
                return session_cart
        else:
            # For anonymous users, try to get their session cart
            cart = cls.objects.filter(session_id=session_id, is_active=True).first()
            if cart:
                return cart
        
        # Create a new cart if we don't have one yet
        return cls.objects.create(
            user=user,
            session_id=session_id,
            is_active=True
        )


class CartItem(UUIDModel, TimestampedModel):
    """
    Shopping cart item model to store items in a cart.
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
        blank=True, null=True
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
        Return the unit price of the product or variant.
        """
        if self.variant:
            return self.variant.price
        return self.product.current_price
    
    @property
    def total_price(self):
        """
        Return the total price for this item.
        """
        return self.unit_price * self.quantity