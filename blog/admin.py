from django.contrib import admin
from django.db import models
from django.contrib.admin.widgets import AdminSplitDateTime
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from tinymce.widgets import TinyMCE
from .models import BlogCategory, BlogPost


class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'post_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    
    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Posts'


class BlogPostAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    list_display = (
        'title',
        'category',
        'status',
        'published_at',
        'is_featured',
        'display_thumbnail',
        'ad_type',
    )
    list_filter = ('status', 'is_featured', 'category', 'ad_type')
    search_fields = ('title', 'content', 'meta_keywords')
    date_hierarchy = 'published_at'
    list_editable = ('status', 'is_featured', 'category')
    list_per_page = 25
    
    fieldsets = (
        ('Post Information', {
            'fields': ('title', 'slug', 'category', 'status', 'is_featured', 'published_at'),
        }),
        ('Content', {
            'fields': ('content',),
        }),
        ('Media', {
            'fields': ('featured_image', 'external_image_url', 'thumbnail', 'youtube_url', 'attachment'),
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
    )
    
    formfield_overrides = {
        models.DateTimeField: {'widget': AdminSplitDateTime},
        models.TextField: {'widget': TinyMCE()},
    }
    
    def display_thumbnail(self, obj):
        """Display post thumbnail in admin list view"""
        if obj.thumbnail:
            return format_html('<img src="{}" width="50" height="auto" />', obj.thumbnail.url)
        elif obj.featured_image:
            return format_html('<img src="{}" width="50" height="auto" />', obj.featured_image.url)
        elif obj.get_youtube_thumbnail():
            return format_html('<img src="{}" width="50" height="auto" />', obj.get_youtube_thumbnail())
        return "No image"
    display_thumbnail.short_description = 'Thumbnail'
    
    def save_model(self, request, obj, form, change):
        # Auto-set the publish date when status is changed to published
        if 'status' in form.changed_data and obj.status == 'published' and not obj.published_at:
            from django.utils import timezone
            obj.published_at = timezone.now()
        super().save_model(request, obj, form, change)
    
    class Media:
        css = {
            'all': ('admin/css/blog_admin.css',)
        }
        js = ('admin/js/blog_admin.js',)


# Register both models
admin.site.register(BlogCategory, BlogCategoryAdmin)
admin.site.register(BlogPost, BlogPostAdmin)