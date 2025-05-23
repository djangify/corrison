from django.db import models
from django.utils.text import slugify
import uuid

class TimestampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    created_at and updated_at fields.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """
    An abstract base class model that provides a UUID id field.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class SluggedModel(models.Model):
    """
    An abstract base class model that provides a slug field that is automatically
    populated from the name field.
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class PublishableModel(models.Model):
    """
    An abstract base class model that provides is_active field for
    enabling/disabling records.
    """
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class SEOModel(models.Model):
    """
    An abstract base class model that provides SEO fields.
    """
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        abstract = True


class ContactMessage(UUIDModel, TimestampedModel):
    """
    Model for storing contact form messages from users.
    """
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_read']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Message from {self.name} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    from django.db import models


class AllowedOrigin(models.Model):
    origin = models.URLField(unique=True)
    note   = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.origin
    
    # Add to core/models.py

class ContactPageSettings(models.Model):
    """
    Model for storing contact page information.
    """
    # Company Address
    address_line1 = models.CharField(max_length=100, blank=True)
    address_line2 = models.CharField(max_length=100, blank=True)
    address_line3 = models.CharField(max_length=100, blank=True)
    address_line4 = models.CharField(max_length=100, blank=True)
    
    # Phone
    phone_number = models.CharField(max_length=50, blank=True)
    business_hours = models.TextField(blank=True, help_text="Enter business hours, one per line")
    
    # Email Addresses
    general_email = models.EmailField(blank=True)
    support_email = models.EmailField(blank=True)
    sales_email = models.EmailField(blank=True)
    
    # Social Media
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    
    # Page Content
    hero_title = models.CharField(max_length=200, default="Get in Touch")
    hero_subtitle = models.TextField(blank=True, default="We'd love to hear from you. Send us a message and we'll respond as soon as possible.")
    form_title = models.CharField(max_length=200, default="Send us a Message")
    
    # Sections Titles
    address_section_title = models.CharField(max_length=100, default="Visit Us")
    phone_section_title = models.CharField(max_length=100, default="Call Us")
    email_section_title = models.CharField(max_length=100, default="Email Us")
    social_section_title = models.CharField(max_length=100, default="Follow Us")
    
    class Meta:
        verbose_name = 'Contact Page Settings'
        verbose_name_plural = 'Contact Page Settings'
    
    def __str__(self):
        return "Contact Page Settings"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and ContactPageSettings.objects.exists():
            return  # Don't allow creating a second instance
        return super().save(*args, **kwargs)