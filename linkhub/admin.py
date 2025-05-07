from django.contrib import admin
from django.db import models
from django.contrib.admin.widgets import AdminSplitDateTime

from .models import LinkHub, Link

@admin.register(LinkHub)
class LinkHubAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}

    list_display = (
        'title',
        'is_published',
        'published_at',
        'created_at',
    )
    list_filter = ('is_published',)

    fields = (
        'title',
        'slug',
        'description',
        'is_published',
        'published_at',
    )

    formfield_overrides = {
        models.DateTimeField: {'widget': AdminSplitDateTime},
    }

@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'page', 'url', 'order')
    list_filter = ('page',)
