from django.db import models
from django.utils.text import slugify

class LinkHub(models.Model):
    slug          = models.SlugField(max_length=100, unique=True)
    title         = models.CharField(max_length=200)
    description   = models.TextField(blank=True)
    background_image = models.ImageField(
        upload_to='linkhub/backgrounds/', 
        blank=True, 
        null=True,
        help_text="Optional background image for the link page"
    )
    created_at    = models.DateTimeField(auto_now_add=True)
    order         = models.PositiveIntegerField(
        default=0,
        help_text="Lower numbers appear first"
    )
    # Publication controls:
    is_published  = models.BooleanField(
        default=False,
        help_text="Publish this hub when checked"
    )
    published_at  = models.DateTimeField(
        null=True, blank=True,
        help_text="Date/time when this hub goes live"
    )

    class Meta:
        ordering = ['order', '-published_at', '-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Link(models.Model):
    """Enhanced Link model that supports different media types"""
    MEDIA_TYPES = (
        ('link', 'Standard Link'),
        ('video', 'Video'),
        ('pdf', 'PDF Document'),
        ('audio', 'Audio/Podcast'),
        ('image', 'Image'),
        ('donation', 'Donation/Tip'),
    )
    
    page          = models.ForeignKey(LinkHub, related_name='links', on_delete=models.CASCADE)
    title         = models.CharField(max_length=100)
    url           = models.URLField()
    media_type    = models.CharField(
        max_length=10, 
        choices=MEDIA_TYPES,
        default='link',
        help_text="Type of media this link represents"
    )
    icon          = models.CharField(
        max_length=100,
        blank=True,
        help_text="Icon name or class (e.g., 'heart', 'star', 'music')"
    )
    description   = models.TextField(
        blank=True, 
        help_text="Short description of this link or media item"
    )
    author        = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Creator or author of this content (optional)"
    )
    order         = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.page.slug} ↦ {self.title}"