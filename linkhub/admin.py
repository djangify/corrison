from django.contrib import admin
from django.db import models
from django.contrib.admin.widgets import AdminSplitDateTime
from django.utils.html import format_html

from .models import LinkHub, Link

class LinkInline(admin.TabularInline):
    model = Link
    extra = 1
    fields = ('title', 'media_type', 'url', 'icon_url', 'description', 'order')

@admin.register(LinkHub)
class LinkHubAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    inlines = [LinkInline]

    list_display = (
        'title',
        'is_published',
        'link_count',
        'published_at',
        'order',
    )
    list_filter = ('is_published',)
    list_editable = ('order',)
    search_fields = ('title', 'description')

    fields = (
        'title',
        'slug',
        'description',
        'background_image',
        'order',
        'is_published',
        'published_at',
    )

    formfield_overrides = {
        models.DateTimeField: {'widget': AdminSplitDateTime},
    }
    
    def link_count(self, obj):
        count = obj.links.count()
        return f"{count} link{'s' if count != 1 else ''}"
    link_count.short_description = "Links"

@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'page', 'media_type', 'preview', 'order')
    list_filter = ('page', 'media_type')
    list_editable = ('order',)
    search_fields = ('title', 'description', 'author')
    
    def preview(self, obj):
        """Show a preview based on media type"""
        if obj.icon_url:
            return format_html('<img src="{}" width="60" height="40" style="object-fit: cover;" />', obj.icon_url)
        
        # Text-based indicators instead of emojis for database compatibility
        media_type_indicators = {
            'video': '[VIDEO]',
            'pdf': '[PDF]',
            'audio': '[AUDIO]',
            'image': '[IMAGE]',
            'link': '[LINK]',
            'donation': '[DONATION]'
        }
        
        return media_type_indicators.get(obj.media_type, '')
    
    preview.short_description = "Preview"