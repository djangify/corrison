from rest_framework import serializers
from .models import SiteSettings, ContactMessage, ContactPageSettings


class SiteSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for Site Settings - used by the API
    """

    logo_url = serializers.SerializerMethodField()
    social_links = serializers.SerializerMethodField()

    class Meta:
        model = SiteSettings
        fields = [
            # Site Information
            "site_name",
            "site_tagline",
            "site_domain",
            "logo_url",  # Computed field
            "favicon",
            # Contact Information
            "contact_email",
            "support_email",
            "sales_email",
            "support_phone",
            # Business Address
            "address_line1",
            "address_line2",
            "city",
            "state",
            "postal_code",
            "country",
            # Social Media Links (computed)
            "social_links",
            # Theme & Design
            "primary_color",
            "secondary_color",
            "accent_color",
            "font_primary",
            "font_headings",
            # Analytics & Tracking
            "google_analytics_id",
            "facebook_pixel_id",
            "google_tag_manager_id",
            # Feature Flags
            "enable_wishlist",
            "enable_reviews",
            "enable_newsletter",
            "enable_blog",
            "enable_cart",
            # E-commerce Settings
            "currency_symbol",
            "currency_code",
            "tax_rate",
            "enabled_payment_methods",
            "shipping_methods",
            # Product Settings
            "products_per_page",
            "related_products_limit",
            "featured_products_limit",
            # Business Info
            "business_hours",
            "footer_copyright_text",
            "footer_description",
            # Timestamps
            "updated_at",
        ]
        read_only_fields = ["updated_at"]

    def get_logo_url(self, obj):
        """Get the appropriate logo URL"""
        return obj.get_logo_url()

    def get_social_links(self, obj):
        """Get social links as a dictionary"""
        return obj.get_social_links()


class ContactMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for Contact Messages - for API submission
    """

    class Meta:
        model = ContactMessage
        fields = [
            "id",
            "name",
            "email",
            "subject",
            "message",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ContactPageSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for Contact Page Settings
    """

    class Meta:
        model = ContactPageSettings
        fields = [
            "title",
            "slug",
            "hero_title",
            "hero_subtitle",
            "form_title",
            "address_section_title",
            "address_line1",
            "address_line2",
            "address_line3",
            "address_line4",
            "phone_section_title",
            "phone_number",
            "business_hours",
            "email_section_title",
            "general_email",
            "support_email",
            "sales_email",
            "social_section_title",
            "facebook_url",
            "instagram_url",
            "twitter_url",
        ]
