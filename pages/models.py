from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError 

class Page(models.Model):
    slug = models.SlugField(max_length=100, unique=True)
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=400, blank=True)
    content = models.TextField(help_text="Rich text / HTML")
    meta_description = models.CharField(max_length=300, blank=True)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Date/time when this page goes live"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Lower numbers appear first"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    hero_title = models.CharField(max_length=200, blank=True)
    hero_subtitle = models.CharField(max_length=300, blank=True)
    hero_content = models.TextField(blank=True, help_text="Rich text for hero section")
    hero_image   = models.ImageField(upload_to="pages/hero/", blank=True, null=True)
    hero_image_url = models.URLField(                 
        blank=True,                                   
        help_text="Public URL of the hero image (leave blank if uploading a file instead)."
    )
    hero_right_content = models.TextField(blank=True, help_text="Optional text content for right side of hero (displays INSTEAD of an image if provided)")

    # Optional call-to-action button in hero section
    hero_button_text = models.CharField(
        max_length=100,
        blank=True,
        help_text="Text for hero CTA button"
    )
    hero_button_url = models.URLField(
        blank=True,
        help_text="URL for hero CTA button"
    )

    # Middle text section
    middle_section_title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Title for middle text section"
    )
    middle_section_content = models.TextField(
        blank=True,
        help_text="Rich text / HTML for middle section"
    )

    # End text section
    end_section_title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Title for end text section"
    )
    end_section_content = models.TextField(
        blank=True,
        help_text="Rich text / HTML for end section"
    )

    # For features/how it works sections
    has_feature_section = models.BooleanField(default=False)
    feature_section_title = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['order', '-updated_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.hero_image and self.hero_image_url:
            raise ValidationError(
                {"hero_image_url": "Choose EITHER an uploaded image OR a URL, not both."}
            )

    # Convenience helper for templates
    def hero_image_src(self):
        """
        Returns the correct URL to render in the template, preferring the
        uploaded file when both are present (shouldn’t happen thanks to clean()).
        """
        if self.hero_image:
            return self.hero_image.url
        return self.hero_image_url or ""

    hero_image_src.short_description = "Hero image source"


class PageFeature(models.Model):
    page = models.ForeignKey(
        Page,
        related_name='features',
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=100, blank=True)
    content = models.TextField()
    icon = models.CharField(
        max_length=100,
        blank=True,
        help_text="Icon name or class"
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
