from django.contrib import admin
from .models import ContactMessage
from .models import AllowedOrigin
from .models import ContactPageSettings

@admin.register(AllowedOrigin)
class AllowedOriginAdmin(admin.ModelAdmin):
    list_display = ('origin', 'note')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    date_hierarchy = 'created_at'
    readonly_fields = ('name', 'email', 'subject', 'message', 'created_at')
    
    def has_add_permission(self, request):
        return False  # Prevent adding messages manually
    
    def has_change_permission(self, request, obj=None):
        # Only allow changing the is_read status
        return True
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields
        return []
    
    def save_model(self, request, obj, form, change):
        # Mark as read when viewed/saved by admin
        if change and not obj.is_read:
            obj.is_read = True
        super().save_model(request, obj, form, change)
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f"{queryset.count()} messages marked as read.")
    mark_as_read.short_description = "Mark selected messages as read"
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, f"{queryset.count()} messages marked as unread.")
    mark_as_unread.short_description = "Mark selected messages as unread"



@admin.register(ContactPageSettings)
class ContactPageSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Hero Section', {
            'fields': ('hero_title', 'hero_subtitle'),
        }),
        ('Form Section', {
            'fields': ('form_title',),
        }),
        ('Address Information', {
            'fields': ('address_section_title', 'address_line1', 'address_line2', 'address_line3', 'address_line4'),
        }),
        ('Phone Information', {
            'fields': ('phone_section_title', 'phone_number', 'business_hours'),
        }),
        ('Email Information', {
            'fields': ('email_section_title', 'general_email', 'support_email', 'sales_email'),
        }),
        ('Social Media', {
            'fields': ('social_section_title', 'facebook_url', 'instagram_url', 'twitter_url'),
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow adding if no instance exists
        return not ContactPageSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the instance
        return False