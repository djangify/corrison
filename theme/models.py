from django.db import models
from django.contrib.auth.models import User
from core.models import TimestampedModel


class Theme(TimestampedModel):
    """
    Theme model for storing theme configuration.
    """
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=False)
    
    # Colors
    primary_color = models.CharField(max_length=20, default="#0d6efd")
    primary_dark_color = models.CharField(max_length=20, default="#0a58ca")
    primary_light_color = models.CharField(max_length=20, default="#6ea8fe")
    
    secondary_color = models.CharField(max_length=20, default="#6c757d")
    secondary_dark_color = models.CharField(max_length=20, default="#5c636a")
    secondary_light_color = models.CharField(max_length=20, default="#a7acb1")
    
    accent_color = models.CharField(max_length=20, default="#fd7e14")
    
    success_color = models.CharField(max_length=20, default="#198754")
    info_color = models.CharField(max_length=20, default="#0dcaf0")
    warning_color = models.CharField(max_length=20, default="#ffc107")
    danger_color = models.CharField(max_length=20, default="#dc3545")
    
    background_color = models.CharField(max_length=20, default="#ffffff")
    text_color = models.CharField(max_length=20, default="#212529")
    
    # Typography
    font_primary = models.CharField(max_length=100, default="'Inter', sans-serif")
    font_headings = models.CharField(max_length=100, default="'Poppins', sans-serif")
    
    # Spacing and Layout
    spacing_unit = models.CharField(max_length=20, default="0.25rem")
    border_radius = models.CharField(max_length=20, default="0.375rem")
    
    # Footer
    footer_background = models.CharField(max_length=20, default="#212529")
    footer_text_color = models.CharField(max_length=20, default="#f8f9fa")
    
    # Buttons
    button_border_radius = models.CharField(max_length=20, default="0.375rem")
    
    # Header
    header_background = models.CharField(max_length=20, default="#ffffff")
    header_text_color = models.CharField(max_length=20, default="#212529")
    
    # Navigation
    nav_background = models.CharField(max_length=20, default="#ffffff")
    nav_text_color = models.CharField(max_length=20, default="#212529")
    nav_active_color = models.CharField(max_length=20, default="#0d6efd")
    
    # Product cards
    product_card_background = models.CharField(max_length=20, default="#ffffff")
    product_card_text_color = models.CharField(max_length=20, default="#212529")
    product_card_border = models.CharField(max_length=20, default="#dee2e6")
    
    # Custom CSS
    custom_css = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Theme'
        verbose_name_plural = 'Themes'
        ordering = ['-is_active', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # If setting this theme as active, deactivate all others
        if self.is_active:
            Theme.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)
    
    @classmethod
    def get_active_theme(cls):
        """
        Get the active theme or return the default theme.
        """
        active_theme = cls.objects.filter(is_active=True).first()
        if not active_theme:
            # If no active theme, get or create the default theme
            active_theme, created = cls.objects.get_or_create(
                name="Default",
                defaults={'is_active': True}
            )
        return active_theme


class SiteSettings(TimestampedModel):
    """
    Site settings model for storing site-specific settings.
    """
    site_name = models.CharField(max_length=100, default="Corrison Store")
    site_description = models.TextField(blank=True, null=True)
    site_logo = models.ImageField(upload_to='site', blank=True, null=True)
    site_favicon = models.ImageField(upload_to='site', blank=True, null=True)
    
    # Contact information
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=50, blank=True, null=True)
    contact_address = models.TextField(blank=True, null=True)
    
    # Social media
    facebook_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    youtube_url = models.URLField(blank=True, null=True)
    
    # Currency and locale
    currency_symbol = models.CharField(max_length=5, default="$")
    currency_code = models.CharField(max_length=5, default="USD")
    
    # SEO
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.CharField(max_length=255, blank=True, null=True)
    
    # Google Analytics
    google_analytics_id = models.CharField(max_length=50, blank=True, null=True)
    
    # Payment methods
    enable_stripe = models.BooleanField(default=True)
    enable_paypal = models.BooleanField(default=False)
    enable_bank_transfer = models.BooleanField(default=False)
    
    # Footer content
    footer_text = models.TextField(blank=True, null=True)
    
    # Legal
    privacy_policy = models.TextField(blank=True, null=True)
    terms_conditions = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'
    
    def __str__(self):
        return self.site_name
    
    @classmethod
    def get_settings(cls):
        """
        Get the site settings or create default settings.
        """
        settings = cls.objects.first()
        if not settings:
            settings = cls.objects.create()
        return settings


class Banner(TimestampedModel):
    """
    Banner model for the homepage carousel.
    """
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='banners')
    url = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Banner'
        verbose_name_plural = 'Banners'
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return self.title


class FooterLink(TimestampedModel):
    """
    Footer link model for the site footer.
    """
    CATEGORY_CHOICES = (
        ('help', 'Help'),
        ('about', 'About Us'),
        ('legal', 'Legal'),
        ('other', 'Other'),
    )
    
    title = models.CharField(max_length=100)
    url = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Footer Link'
        verbose_name_plural = 'Footer Links'
        ordering = ['category', 'order']
    
    def __str__(self):
        return self.title
    