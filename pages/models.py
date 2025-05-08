from django.db import models
from django.utils.text import slugify

class Page(models.Model):
    slug             = models.SlugField(max_length=100, unique=True)
    title            = models.CharField(max_length=200)
    subtitle         = models.CharField(max_length=400, blank=True)
    hero_image       = models.ImageField(upload_to="pages/hero/", blank=True, null=True)
    content          = models.TextField(help_text="Rich text / HTML")
    meta_description = models.CharField(max_length=300, blank=True)
    is_published     = models.BooleanField(default=False)
    published_at     = models.DateTimeField(
        null=True, blank=True,
        help_text="Date/time when this page goes live"
    )
    order            = models.PositiveIntegerField(
        default=0,
        help_text="Lower numbers appear first"
    )
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    hero_title = models.CharField(max_length=200, blank=True)
    hero_subtitle = models.CharField(max_length=300, blank=True)
    hero_image = models.ImageField(upload_to="pages/hero/", blank=True, null=True)
    hero_content = models.TextField(blank=True, help_text="Rich text for hero section")
    
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

class PageFeature(models.Model):
    page = models.ForeignKey(Page, related_name='features', on_delete=models.CASCADE)
    title = models.CharField(max_length=100, blank=True)
    content = models.TextField()
    icon = models.CharField(max_length=100, blank=True, help_text="Icon name or class")
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
