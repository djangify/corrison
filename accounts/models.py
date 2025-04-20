from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import TimestampedModel, UUIDModel


class Profile(TimestampedModel):
    """
    User profile model to extend Django's built-in User model.
    """
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, 
        related_name='profile'
    )
    phone = models.CharField(max_length=50, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    
    # Preferences
    email_marketing = models.BooleanField(default=False)
    receive_order_updates = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'
        indexes = [
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"Profile for {self.user.email}"


class WishlistItem(UUIDModel, TimestampedModel):
    """
    Wishlist item model to store items in a user's wishlist.
    """
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, 
        related_name='wishlist_items'
    )
    product = models.ForeignKey(
        'products.Product', on_delete=models.CASCADE,
        related_name='wishlist_items'
    )
    
    class Meta:
        verbose_name = 'Wishlist Item'
        verbose_name_plural = 'Wishlist Items'
        unique_together = ('user', 'product')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['product']),
        ]
    
    def __str__(self):
        return f"{self.product.name} in {self.user.username}'s wishlist"