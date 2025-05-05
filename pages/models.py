from django.db import models
from django.utils.text import slugify

class Page(models.Model):
    slug            = models.SlugField(max_length=100, unique=True)
    title           = models.CharField(max_length=200)
    subtitle        = models.CharField(max_length=400, blank=True)
    hero_image      = models.ImageField(upload_to="pages/hero/", blank=True, null=True)
    content         = models.TextField(help_text="Rich text / HTML")
    meta_description = models.CharField(max_length=300, blank=True)
    is_published    = models.BooleanField(default=False)
    order           = models.PositiveIntegerField(default=0,
                        help_text="Lower numbers appear first (for e.g. feature lists)")
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-updated_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title