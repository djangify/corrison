from django.contrib import admin
from .models import ContactMessage, AllowedOrigin, ContactPageSettings, SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """
    Admin interface for Site Settings - singleton model
    """

    def has_add_permission(self, request):
        # Only allow one instance
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of site settings
        return False

    fieldsets = (
        (
            "Site Information",
            {
                "fields": (
                    "site_name",
                    "site_tagline",
                    "site_domain",
                    "site_logo",
                    "site_logo_url",
                    "favicon",
                ),
                "description": "Basic site information and branding",
            },
        ),
        (
            "Contact Information",
            {
                "fields": (
                    "contact_email",
                    "support_email",
                    "sales_email",
                    "support_phone",
                ),
            },
        ),
        (
            "Business Address",
            {
                "fields": (
                    "address_line1",
                    "address_line2",
                    "city",
                    "state",
                    "postal_code",
                    "country",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Social Media Links",
            {
                "fields": (
                    "facebook_url",
                    "instagram_url",
                    "twitter_url",
                    "youtube_url",
                    "linkedin_url",
                    "tiktok_url",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Theme & Design",
            {
                "fields": (
                    "primary_color",
                    "secondary_color",
                    "accent_color",
                    "font_primary",
                    "font_headings",
                ),
                "description": "Colors and typography settings",
            },
        ),
        (
            "Analytics & Tracking",
            {
                "fields": (
                    "google_analytics_id",
                    "facebook_pixel_id",
                    "google_tag_manager_id",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Feature Flags",
            {
                "fields": (
                    "enable_wishlist",
                    "enable_reviews",
                    "enable_newsletter",
                    "enable_blog",
                    "enable_cart",
                ),
                "description": "Enable/disable site features",
            },
        ),
        (
            "E-commerce Settings",
            {
                "fields": (
                    "currency_symbol",
                    "currency_code",
                    "tax_rate",
                    "enabled_payment_methods",
                    "shipping_methods",
                ),
            },
        ),
        (
            "Product Display Settings",
            {
                "fields": (
                    "products_per_page",
                    "related_products_limit",
                    "featured_products_limit",
                ),
            },
        ),
        (
            "Business Info",
            {
                "fields": (
                    "business_hours",
                    "footer_copyright_text",
                    "footer_description",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at")

    def changelist_view(self, request, extra_context=None):
        # Redirect to the single instance edit page if it exists
        if SiteSettings.objects.exists():
            settings = SiteSettings.objects.first()
            return self.change_view(request, str(settings.pk), extra_context)
        return super().changelist_view(request, extra_context)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "email", "subject")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("name", "email", "subject", "message", "is_read")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(AllowedOrigin)
class AllowedOriginAdmin(admin.ModelAdmin):
    list_display = ("origin", "note")
    search_fields = ("origin", "note")


@admin.register(ContactPageSettings)
class ContactPageSettingsAdmin(admin.ModelAdmin):
    """
    Admin interface for Contact Page Settings
    """

    def has_add_permission(self, request):
        # Only allow one instance
        return not ContactPageSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of contact page settings
        return False

    fieldsets = (
        (
            "Page Info",
            {
                "fields": ("title", "slug"),
            },
        ),
        (
            "Hero Section",
            {
                "fields": ("hero_title", "hero_subtitle"),
            },
        ),
        (
            "Form Section",
            {
                "fields": ("form_title",),
            },
        ),
        (
            "Address Information",
            {
                "fields": (
                    "address_section_title",
                    "address_line1",
                    "address_line2",
                    "address_line3",
                    "address_line4",
                ),
            },
        ),
        (
            "Phone Information",
            {
                "fields": (
                    "phone_section_title",
                    "phone_number",
                    "business_hours",
                ),
            },
        ),
        (
            "Email Addresses",
            {
                "fields": (
                    "email_section_title",
                    "general_email",
                    "support_email",
                    "sales_email",
                ),
            },
        ),
        (
            "Social Media",
            {
                "fields": (
                    "social_section_title",
                    "facebook_url",
                    "instagram_url",
                    "twitter_url",
                ),
            },
        ),
    )

    prepopulated_fields = {"slug": ("title",)}

    def changelist_view(self, request, extra_context=None):
        # Redirect to the single instance edit page if it exists
        if ContactPageSettings.objects.exists():
            settings = ContactPageSettings.objects.first()
            return self.change_view(request, str(settings.pk), extra_context)
        return super().changelist_view(request, extra_context)
