from django.contrib import admin
from .models import ContactMessage
from .models import AllowedOrigin

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
    