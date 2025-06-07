from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import TimestampedModel, UUIDModel
import uuid
from django.utils import timezone


class Profile(TimestampedModel):
    """
    User profile model to extend Django's built-in User model.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=50, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)

    # Preferences
    email_marketing = models.BooleanField(default=False)
    receive_order_updates = models.BooleanField(default=True)

    # Email verification fields
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=255, blank=True)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)

    # password reset:
    password_reset_token = models.CharField(max_length=255, blank=True)
    password_reset_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["email_verification_token"]),
        ]

    def __str__(self):
        return f"Profile for {self.user.email}"

    def generate_verification_token(self):
        """Generate a new email verification token"""
        self.email_verification_token = str(uuid.uuid4())
        self.email_verification_sent_at = timezone.now()
        self.save()
        return self.email_verification_token

    def generate_password_reset_token(self):
        """Generate a new password reset token"""
        self.password_reset_token = str(uuid.uuid4())
        self.password_reset_sent_at = timezone.now()
        self.save()
        return self.password_reset_token


class WishlistItem(UUIDModel, TimestampedModel):
    """
    Wishlist item model to store items in a user's wishlist.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="wishlist_items"
    )
    product = models.ForeignKey(
        "products.Product", on_delete=models.CASCADE, related_name="wishlist_items"
    )

    class Meta:
        verbose_name = "Wishlist Item"
        verbose_name_plural = "Wishlist Items"
        unique_together = ("user", "product")
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["product"]),
        ]

    def __str__(self):
        return f"{self.product.name} in {self.user.username}'s wishlist"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create profile when user is created"""
    if created:
        # Auto-verify superusers
        email_verified = instance.is_superuser
        Profile.objects.create(user=instance, email_verified=email_verified)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save profile when user is saved"""
    if hasattr(instance, "profile"):
        instance.profile.save()
