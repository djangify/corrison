from django.contrib import admin
from django.db import models
from django.contrib.admin.widgets import AdminSplitDateTime

from .models import Page

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}

    list_display = (
        'title',
        'is_published',
        'published_at',
        'order',
    )
    list_filter = ('is_published',)

    fields = (
        'title',
        'slug',
        'subtitle',
        'hero_image',
        'content',
        'meta_description',
        'is_published',
        'published_at',
        'order',
    )

    formfield_overrides = {
        models.DateTimeField: {'widget': AdminSplitDateTime},
    }
