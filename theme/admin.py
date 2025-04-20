from django.contrib import admin
from .models import Theme, SiteSettings, Banner, FooterLink


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name',)
    list_editable = ('is_active',)
    fieldsets = (
        (None, {
            'fields': ('name', 'is_active')
        }),
        ('Colors', {
            'fields': (
                'primary_color', 'primary_dark_color', 'primary_light_color',
                'secondary_color', 'secondary_dark_color', 'secondary_light_color',
                'accent_color', 'success_color', 'info_color', 'warning_color', 'danger_color',
                'background_color', 'text_color'
            ),
            'classes': ('wide',)
        }),
        ('Typography', {
            'fields': ('font_primary', 'font_headings')
        }),
        ('Layout', {
            'fields': ('spacing_unit', 'border_radius')
        }),
        ('Footer', {
            'fields': ('footer_background', 'footer_text_color')
        }),
        ('Buttons', {
            'fields': ('button_border_radius',)
        }),
        ('Header', {
            'fields': ('header_background', 'header_text_color')
        }),
        ('Navigation', {
            'fields': ('nav_background', 'nav_text_color', 'nav_active_color')
        }),
        ('Product Cards', {
            'fields': ('product_card_background', 'product_card_text_color', 'product_card_border')
        }),
        ('Custom CSS', {
            'fields': ('custom_css',)
        }),
    )
    save_on_top = True


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'contact_email', 'currency_code', 'updated_at')
    fieldsets = (
        ('Site Information', {
            'fields': ('site_name', 'site_description', 'site_logo', 'site_favicon')
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'contact_phone', 'contact_address')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'twitter_url', 'instagram_url', 'youtube_url')
        }),
        ('Currency and Locale', {
            'fields': ('currency_symbol', 'currency_code')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords')
        }),
        ('Analytics', {
            'fields': ('google_analytics_id',)
        }),
        ('Payment Methods', {
            'fields': ('enable_stripe', 'enable_paypal', 'enable_bank_transfer')
        }),
        ('Footer Content', {
            'fields': ('footer_text',)
        }),
        ('Legal', {
            'fields': ('privacy_policy', 'terms_conditions')
        }),
    )

    def has_add_permission(self, request):
        # Prevent creating more than one SiteSettings instance
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deleting the SiteSettings instance
        return False


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'subtitle')
    list_editable = ('order', 'is_active')


@admin.register(FooterLink)
class FooterLinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'url', 'order', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('title', 'url')
    list_editable = ('category', 'order', 'is_active')
    