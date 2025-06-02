# pages/admin.py

from django.contrib import admin
from django.db import models
from django.contrib.admin.widgets import AdminSplitDateTime
from tinymce.widgets import TinyMCE
from .models import Page, PageFeature


class PageFeatureInline(admin.TabularInline):
    model = PageFeature
    extra = 1
    formfield_overrides = {
        models.TextField: {"widget": TinyMCE(attrs={"cols": 80, "rows": 10})},
    }


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    inlines = [PageFeatureInline]

    list_display = (
        "title",
        "is_published",
        "published_at",
        "order",
    )
    list_filter = ("is_published",)

    fieldsets = (
        # 1. Title block
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "subtitle",
                ),
            },
        ),
        # 2. Hero
        (
            "Hero Section",
            {
                "fields": (
                    "hero_title",
                    "hero_subtitle",
                    "hero_image",
                    "hero_image_url",
                    "hero_content",
                    "hero_right_content",
                    "hero_button_text",
                    "hero_button_url",
                ),
            },
        ),
        # 3. Main content
        (
            "Content",
            {
                "fields": ("content",),
            },
        ),
        # 4. Feature section
        (
            "Feature Section",
            {
                "fields": ("has_feature_section", "feature_section_title"),
            },
        ),
        # 5. Middle section
        (
            "Middle Section",
            {
                "fields": ("middle_section_title", "middle_section_content"),
            },
        ),
        # 6. End section
        (
            "End Section",
            {
                "fields": ("end_section_title", "end_section_content"),
            },
        ),
        # 7. Publishing controls
        (
            "Publishing",
            {
                "fields": (
                    "is_published",
                    "published_at",
                    "order",
                    "meta_description",
                ),
            },
        ),
        # 8. Timestamps
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    formfield_overrides = {
        models.DateTimeField: {"widget": AdminSplitDateTime},
        models.TextField: {"widget": TinyMCE(attrs={"cols": 80, "rows": 20})},
    }
