# pages/admin.py

from django.contrib import admin
from django.db import models
from django.contrib.admin.widgets import AdminSplitDateTime
from tinymce.widgets import TinyMCE
from .models import Page, PageFeature, Testimonial, PageTestimonial


class PageFeatureInline(admin.TabularInline):
    model = PageFeature
    extra = 1


class PageTestimonialInline(admin.TabularInline):
    model = PageTestimonial
    extra = 1
    autocomplete_fields = ["testimonial"]
    verbose_name = "Testimonial"
    verbose_name_plural = "Testimonials for this page"


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "company",
        "category",
        "rating",
        "is_featured",
        "order",
        "created_at",
    )
    list_filter = ("category", "rating", "is_featured", "created_at")
    search_fields = ("name", "company", "content", "title")
    list_editable = ("order", "is_featured", "category")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("name", "title", "company", "category")}),
        ("Testimonial Content", {"fields": ("content", "rating", "image")}),
        ("Display Options", {"fields": ("is_featured", "order")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    formfield_overrides = {
        models.TextField: {"widget": TinyMCE(attrs={"cols": 80, "rows": 10})},
    }


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    inlines = [PageFeatureInline, PageTestimonialInline]
    search_fields = ("title", "content", "meta_description")

    list_display = (
        "title",
        "page_type",
        "is_published",
        "published_at",
        "order",
    )
    list_filter = ("is_published", "page_type", "created_at")

    fieldsets = (
        # 1. Basic Information
        (
            None,
            {
                "fields": ("title", "slug", "subtitle", "page_type"),
            },
        ),
        # 2. Hero Section - Basic
        (
            "Hero Section - Basic",
            {
                "fields": (
                    "hero_title",
                    "hero_subtitle",
                    "hero_image",
                    "hero_image_url",
                    "hero_content",
                    "hero_right_content",
                ),
            },
        ),
        # 3. Hero Section - CTAs
        (
            "Hero Section - Call to Action Buttons",
            {
                "fields": (
                    "hero_button_text",
                    "hero_button_url",
                    "hero_button_2_text",
                    "hero_button_2_url",
                ),
            },
        ),
        # 4. Landing Page Features
        (
            "Landing Page Features",
            {
                "fields": (
                    "hero_video_url",
                    "show_prelaunch_badge",
                    "prelaunch_badge_text",
                    "show_countdown",
                    "countdown_target_date",
                    "countdown_title",
                    "show_social_proof",
                    "social_proof_title",
                    "show_scroll_indicator",
                ),
                "classes": ("collapse",),
                "description": "These features are primarily for landing pages but can be used on any page type.",
            },
        ),
        # 5. Main Content
        (
            "Content",
            {
                "fields": ("content",),
            },
        ),
        # 6. Feature Section
        (
            "Feature Section",
            {
                "fields": ("has_feature_section", "feature_section_title"),
            },
        ),
        # 7. Middle Section
        (
            "Middle Section",
            {
                "fields": ("middle_section_title", "middle_section_content"),
            },
        ),
        # 8. End Section
        (
            "End Section",
            {
                "fields": ("end_section_title", "end_section_content"),
            },
        ),
        # 9. SEO & Publishing
        (
            "SEO & Publishing",
            {
                "fields": (
                    "meta_description",
                    "is_published",
                    "published_at",
                    "order",
                ),
            },
        ),
        # 10. Timestamps
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at")

    formfield_overrides = {
        models.DateTimeField: {"widget": AdminSplitDateTime},
        models.TextField: {"widget": TinyMCE(attrs={"cols": 80, "rows": 20})},
    }

    class Media:
        css = {
            "all": ("admin/css/landing-pages.css",)  # Optional: custom admin styling
        }

    def get_queryset(self, request):
        """Optimize queryset to reduce database queries"""
        return (
            super()
            .get_queryset(request)
            .select_related()
            .prefetch_related("features", "page_testimonials__testimonial")
        )

    def save_model(self, request, obj, form, change):
        """Custom save logic if needed"""
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        """Customize form based on page type"""
        form = super().get_form(request, obj, **kwargs)

        # Add help text or modify fields based on page type
        if obj and obj.page_type == "landing":
            pass  # Could add landing-specific form modifications here

        return form
