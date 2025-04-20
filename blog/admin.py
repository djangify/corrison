from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Post

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'featured', 'publish_date', 'display_image')
    list_filter = ('status', 'featured', 'category', 'publish_date')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'publish_date'
    readonly_fields = ('created', 'updated')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'category', 'status', 'featured', 'publish_date')
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('Media', {
            'fields': ('image', 'external_image_url', 'youtube_url', 'thumbnail'),
            'classes': ('collapse',),
        }),
        ('Advertisement', {
            'fields': ('ad_type', 'ad_code', 'ad_image', 'ad_url'),
            'classes': ('collapse',),
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',),
        }),
    )
    
    def display_image(self, obj):
        if obj.get_image_url():
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.get_image_url())
        return "No image"
    display_image.short_description = 'Image'
    