from django.contrib import admin
from django.db import models
from django.contrib.admin.widgets import AdminSplitDateTime

from .models import BlogPost

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}

    list_display = (
        'title',
        'is_published',
        'published_at',
        'is_featured',
        'created_at',
    )
    list_filter = ('is_published', 'is_featured')

    fields = (
        'title',
        'slug',
        'content',
        'featured_image',
        'youtube_url',
        'attachment',
        'is_featured',
        'is_published',
        'published_at',
    )

    formfield_overrides = {
        models.DateTimeField: {'widget': AdminSplitDateTime},
    }
