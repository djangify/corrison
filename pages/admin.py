from django.contrib import admin
from django.db import models
from django.contrib.admin.widgets import AdminSplitDateTime
from .models import Page, PageFeature


class PageFeatureInline(admin.TabularInline):
    model = PageFeature
    extra = 1

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    inlines = [PageFeatureInline]

    list_display = (
        'title',
        'is_published',
        'published_at',
        'order',
    )
    list_filter = ('is_published',)

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'subtitle', 'content')
        }),
        ('Hero Section', {
            'fields': ('hero_title', 'hero_subtitle', 'hero_image', 'hero_content'),
        }),
        ('Feature Section', {
            'fields': ('has_feature_section', 'feature_section_title'),
        }),
        ('Publishing', {
            'fields': ('is_published', 'published_at', 'order', 'meta_description'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_at', 'updated_at',)

    formfield_overrides = {
        models.DateTimeField: {'widget': AdminSplitDateTime},
    }