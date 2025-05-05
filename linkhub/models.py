from django.db import models
from django.utils.text import slugify

class LinkHub(models.Model):
    slug        = models.SlugField(max_length=100, unique=True)
    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Link(models.Model):
    page     = models.ForeignKey(LinkHub, related_name='links', on_delete=models.CASCADE)
    title    = models.CharField(max_length=100)
    url      = models.URLField()
    icon_url = models.URLField(blank=True, help_text="Optional icon or avatar")
    order    = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.page.slug} ↦ {self.title}"
