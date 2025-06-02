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


class SiteSettings(models.Model):
    """
    Singleton model for site-wide settings that replaces static site_settings.py
    """

    # Site Information
    site_name = models.CharField(max_length=100, default="Corrison Store")
    site_tagline = models.CharField(
        max_length=200, blank=True, help_text="Short description/tagline for your site"
    )
    site_domain = models.CharField(max_length=100, default="example.com")
    site_logo = models.ImageField(upload_to="site/logos/", blank=True, null=True)
    site_logo_url = models.URLField(
        blank=True, help_text="Alternative to uploading logo file"
    )
    favicon = models.ImageField(upload_to="site/favicons/", blank=True, null=True)

    # Contact Information
    contact_email = models.EmailField(default="contact@example.com")
    support_email = models.EmailField(blank=True)
    sales_email = models.EmailField(blank=True)
    support_phone = models.CharField(max_length=20, default="+1 123-456-7890")

    # Business Address
    address_line1 = models.CharField(max_length=100, blank=True)
    address_line2 = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=50, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=50, blank=True)

    # Social Media Links
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)

    # Theme & Design Settings
    primary_color = models.CharField(
        max_length=7, default="#0d6efd", help_text="Hex color code (e.g., #0d6efd)"
    )
    secondary_color = models.CharField(
        max_length=7, default="#6c757d", help_text="Hex color code (e.g., #6c757d)"
    )
    accent_color = models.CharField(
        max_length=7, default="#fd7e14", help_text="Hex color code (e.g., #fd7e14)"
    )
    font_primary = models.CharField(max_length=100, default="'Inter', sans-serif")
    font_headings = models.CharField(max_length=100, default="'Poppins', sans-serif")

    # Analytics & Tracking
    google_analytics_id = models.CharField(
        max_length=50, blank=True, help_text="Google Analytics tracking ID"
    )
    facebook_pixel_id = models.CharField(
        max_length=50, blank=True, help_text="Facebook Pixel ID"
    )
    google_tag_manager_id = models.CharField(
        max_length=50, blank=True, help_text="Google Tag Manager ID"
    )

    # Feature Flags
    enable_wishlist = models.BooleanField(default=True)
    enable_reviews = models.BooleanField(default=True)
    enable_newsletter = models.BooleanField(default=True)
    enable_blog = models.BooleanField(default=True)
    enable_cart = models.BooleanField(default=True)

    # E-commerce Settings
    currency_symbol = models.CharField(max_length=5, default="$")
    currency_code = models.CharField(max_length=3, default="USD")
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=0.10,
        help_text="Tax rate as decimal (e.g., 0.10 for 10%)",
    )

    # Payment Methods - JSON field for flexibility
    enabled_payment_methods = models.JSONField(
        default=list,
        blank=True,
        help_text='JSON array of enabled payment methods, e.g., ["stripe", "paypal"]',
    )

    # Shipping Methods - JSON field for flexibility
    shipping_methods = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON object with shipping method configurations",
    )

    # Product Settings
    products_per_page = models.PositiveIntegerField(default=12)
    related_products_limit = models.PositiveIntegerField(default=4)
    featured_products_limit = models.PositiveIntegerField(default=8)

    # Business Hours & Info
    business_hours = models.TextField(
        blank=True, help_text="Enter business hours, one per line"
    )
    footer_copyright_text = models.CharField(max_length=200, blank=True)
    footer_description = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def save(self, *args, **kwargs):
        # Ensure only one instance exists (singleton pattern)
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Prevent deletion of the singleton instance
        pass

    @classmethod
    def get_settings(cls):
        """Get or create the site settings instance"""
        settings, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                "enabled_payment_methods": ["stripe", "paypal"],
                "shipping_methods": {
                    "standard": {
                        "name": "Standard Shipping",
                        "price": 5.00,
                        "description": "3-5 business days",
                    },
                    "express": {
                        "name": "Express Shipping",
                        "price": 15.00,
                        "description": "1-2 business days",
                    },
                },
            },
        )
        return settings

    def __str__(self):
        return f"Site Settings - {self.site_name}"

    def get_logo_url(self):
        """Return the appropriate logo URL"""
        if self.site_logo:
            return self.site_logo.url
        return self.site_logo_url or ""

    def get_social_links(self):
        """Return a dictionary of social links (similar to your original SOCIAL_LINKS)"""
        return {
            "facebook": self.facebook_url,
            "instagram": self.instagram_url,
            "twitter": self.twitter_url,
            "youtube": self.youtube_url,
            "linkedin": self.linkedin_url,
            "tiktok": self.tiktok_url,
        }


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
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_read"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return (
            f"Message from {self.name} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        )


class AllowedOrigin(models.Model):
    origin = models.URLField(unique=True)
    note = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.origin


class ContactPageSettings(models.Model):
    """
    Model for storing contact page information.
    """

    # Title and Slug
    title = models.CharField(max_length=100, default="Contact Us")
    slug = models.SlugField(max_length=100, unique=True, default="contact")

    # Hero Section
    hero_title = models.CharField(max_length=200, default="Get in Touch")
    hero_subtitle = models.TextField(
        blank=True,
        default="We'd love to hear from you. Send us a message and we'll respond as soon as possible.",
    )

    # Form Section
    form_title = models.CharField(max_length=200, default="Send us a Message")

    # Address Information
    address_section_title = models.CharField(max_length=100, default="Visit Us")
    address_line1 = models.CharField(max_length=100, blank=True)
    address_line2 = models.CharField(max_length=100, blank=True)
    address_line3 = models.CharField(max_length=100, blank=True)
    address_line4 = models.CharField(max_length=100, blank=True)

    # Phone Information
    phone_section_title = models.CharField(max_length=100, default="Call Us")
    phone_number = models.CharField(max_length=50, blank=True)
    business_hours = models.TextField(
        blank=True, help_text="Enter business hours, one per line"
    )

    # Email Addresses
    email_section_title = models.CharField(max_length=100, default="Email Us")
    general_email = models.EmailField(blank=True)
    support_email = models.EmailField(blank=True)
    sales_email = models.EmailField(blank=True)

    # Social Media
    social_section_title = models.CharField(max_length=100, default="Follow Us")
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)

    class Meta:
        verbose_name = "Contact Page Settings"
        verbose_name_plural = "Contact Page Settings"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Ensure slug is created from title
        if not self.slug:
            self.slug = slugify(self.title)

        # Ensure only one instance exists
        if not self.pk and ContactPageSettings.objects.exists():
            return  # Don't allow creating a second instance
        return super().save(*args, **kwargs)
