from django.db import models
from django.utils.text import slugify
from tinymce.models import HTMLField

class BlogPost(models.Model):
    title          = models.CharField(max_length=200)
    slug           = models.SlugField(unique=True, blank=True)
    content        = HTMLField()
    created_at     = models.DateTimeField(auto_now_add=True)
    # New fields:
    is_published   = models.BooleanField(
        default=False,
        help_text="Publish this post when checked"
    )
    published_at   = models.DateTimeField(
        null=True, blank=True,
        help_text="Date/time when this post goes live"
    )

    featured_image = models.ImageField(
        upload_to='blog/images/',
        blank=True, null=True,
        help_text='Optional main image for the post'
    )
    youtube_url    = models.URLField(
        blank=True,
        help_text='Optional YouTube embed URL'
    )
    attachment     = models.FileField(
        upload_to='blog/attachments/',
        blank=True, null=True,
        help_text='Optional file to download'
    )
    is_featured    = models.BooleanField(
        default=False,
        help_text="Flag featured posts"
    )

    class Meta:
        ordering = ['-published_at', '-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
