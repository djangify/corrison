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
        null=True, blank=True, help_text="Date/time when this page goes live"
    )
    order = models.PositiveIntegerField(
        default=0, help_text="Lower numbers appear first"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Page type - NEW FIELD
    page_type = models.CharField(
        max_length=20,
        choices=[("page", "Regular Page"), ("landing", "Landing Page")],
        default="page",
        help_text="Type of page - affects available features",
    )

    # Existing hero fields
    hero_title = models.CharField(max_length=200, blank=True)
    hero_subtitle = models.CharField(max_length=300, blank=True)
    hero_content = models.TextField(blank=True, help_text="Rich text for hero section")
    hero_image = models.ImageField(upload_to="pages/hero/", blank=True, null=True)
    hero_image_url = models.URLField(
        blank=True,
        help_text="Public URL of the hero image (leave blank if uploading a file instead).",
    )
    hero_right_content = models.TextField(
        blank=True,
        help_text="Optional text content for right side of hero (displays INSTEAD of an image if provided)",
    )

    # Existing CTA button
    hero_button_text = models.CharField(
        max_length=100, blank=True, help_text="Text for hero CTA button"
    )
    hero_button_url = models.URLField(blank=True, help_text="URL for hero CTA button")

    # NEW LANDING PAGE HERO ENHANCEMENTS
    hero_video_url = models.URLField(
        blank=True,
        help_text="External video URL (YouTube, Vimeo, etc.) for hero background",
    )
    show_prelaunch_badge = models.BooleanField(
        default=False, help_text="Show 'Coming Soon' or custom badge in hero"
    )
    prelaunch_badge_text = models.CharField(
        max_length=50,
        default="Coming Soon",
        blank=True,
        help_text="Text for prelaunch badge",
    )

    # NEW COUNTDOWN TIMER FIELDS
    show_countdown = models.BooleanField(
        default=False, help_text="Display countdown timer in hero section"
    )
    countdown_target_date = models.DateTimeField(
        blank=True, null=True, help_text="Target date/time for countdown timer"
    )
    countdown_title = models.CharField(
        max_length=100, blank=True, help_text="Title above countdown timer"
    )

    # NEW SECONDARY CTA BUTTON
    hero_button_2_text = models.CharField(
        max_length=100, blank=True, help_text="Text for secondary CTA button"
    )
    hero_button_2_url = models.URLField(
        blank=True, help_text="URL for secondary CTA button"
    )

    # NEW SOCIAL PROOF SECTION
    show_social_proof = models.BooleanField(
        default=False, help_text="Display social proof section with testimonials"
    )
    social_proof_title = models.CharField(
        max_length=100, blank=True, help_text="Title for social proof section"
    )

    # NEW UI ENHANCEMENTS
    show_scroll_indicator = models.BooleanField(
        default=True, help_text="Show scroll down indicator in hero section"
    )

    # Existing content sections
    middle_section_title = models.CharField(
        max_length=200, blank=True, help_text="Title for middle text section"
    )
    middle_section_content = models.TextField(
        blank=True, help_text="Rich text / HTML for middle section"
    )

    end_section_title = models.CharField(
        max_length=200, blank=True, help_text="Title for end text section"
    )
    end_section_content = models.TextField(
        blank=True, help_text="Rich text / HTML for end section"
    )

    # Existing features section
    has_feature_section = models.BooleanField(default=False)
    feature_section_title = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["order", "-updated_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.get_page_type_display()})"

    def clean(self):
        super().clean()
        if self.hero_image and self.hero_image_url:
            raise ValidationError(
                {
                    "hero_image_url": "Choose EITHER an uploaded image OR a URL, not both."
                }
            )

        # Validate countdown fields
        if self.show_countdown and not self.countdown_target_date:
            raise ValidationError(
                {
                    "countdown_target_date": "Target date is required when countdown is enabled."
                }
            )

    # Convenience helper for templates
    def hero_image_src(self):
        """
        Returns the correct URL to render in the template, preferring the
        uploaded file when both are present (shouldn't happen thanks to clean()).
        """
        if self.hero_image:
            return self.hero_image.url
        return self.hero_image_url or ""

    hero_image_src.short_description = "Hero image source"

    def is_landing_page(self):
        """Check if this is a landing page"""
        return self.page_type == "landing"


class PageFeature(models.Model):
    page = models.ForeignKey(Page, related_name="features", on_delete=models.CASCADE)
    title = models.CharField(max_length=100, blank=True)
    content = models.TextField()
    icon = models.CharField(max_length=100, blank=True, help_text="Icon name or class")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.page.title} - {self.title or 'Feature'}"


class Testimonial(models.Model):
    """Global testimonials that can be reused across multiple pages"""

    name = models.CharField(max_length=100)
    title = models.CharField(max_length=100, blank=True, help_text="Job title or role")
    company = models.CharField(max_length=100, blank=True)
    content = models.TextField(help_text="Testimonial content")
    image = models.ImageField(
        upload_to="testimonials/",
        blank=True,
        null=True,
        help_text="Photo of the person giving testimonial",
    )
    rating = models.PositiveIntegerField(
        choices=[(i, i) for i in range(1, 6)], default=5, help_text="Star rating (1-5)"
    )
    category = models.CharField(
        max_length=50,
        blank=True,
        help_text="Category for filtering (e.g., 'product', 'service', 'general')",
    )
    is_featured = models.BooleanField(
        default=False, help_text="Mark as featured testimonial"
    )
    order = models.PositiveIntegerField(
        default=0, help_text="Display order (lower numbers first)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "-created_at"]

    def __str__(self):
        if self.company:
            return f"{self.name} - {self.company}"
        return self.name


class PageTestimonial(models.Model):
    """Link testimonials to specific pages"""

    page = models.ForeignKey(
        Page, related_name="page_testimonials", on_delete=models.CASCADE
    )
    testimonial = models.ForeignKey(Testimonial, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(
        default=0, help_text="Display order on this page"
    )

    class Meta:
        ordering = ["order"]
        unique_together = ["page", "testimonial"]

    def __str__(self):
        return f"{self.page.title} - {self.testimonial.name}"
