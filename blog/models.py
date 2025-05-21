from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from tinymce.models import HTMLField
from core.models import TimestampedModel


class BlogCategory(TimestampedModel):
    """
    Category model for blog posts.
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Blog Category"
        verbose_name_plural = "Blog Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("blog:category", kwargs={"slug": self.slug})
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BlogPost(TimestampedModel):
    """
    Enhanced blog post model with additional features.
    """
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]
    
    AD_TYPE_CHOICES = [
        ("none", "No Advertisement"),
        ("adsense", "Google AdSense"),
        ("banner", "Banner Image"),
    ]
    
    # Basic fields
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(
        BlogCategory, 
        on_delete=models.PROTECT, 
        related_name="posts",
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default="draft"
    )
    is_featured = models.BooleanField(
        default=False, 
        help_text="Feature this post on the homepage"
    )
    
    # Publication fields
    published_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Date/time when this post goes live"
    )
    
    # Content
    content = HTMLField("Content")
    
    # Media fields
    featured_image = models.ImageField(
        upload_to='blog/images/',
        blank=True, 
        null=True,
        help_text='Main image for the post'
    )
    external_image_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="External URL for post image (use instead of uploading)"
    )
    youtube_url = models.URLField(
        blank=True,
        help_text='YouTube embed URL'
    )
    thumbnail = models.ImageField(
        upload_to="blog/thumbnails/", 
        null=True, 
        blank=True,
        help_text="Small image for listings (falls back to main image if not provided)"
    )
    attachment = models.FileField(
        upload_to='blog/attachments/',
        blank=True, 
        null=True,
        help_text='Optional file for users to download'
    )
    
    # Advertisement fields
    ad_type = models.CharField(
        max_length=10, 
        choices=AD_TYPE_CHOICES, 
        default="none"
    )
    ad_code = HTMLField(
        blank=True,
        help_text="HTML/JavaScript ad code (for AdSense)"
    )
    ad_image = models.ImageField(
        upload_to="blog/ads/", 
        null=True, 
        blank=True,
        help_text="Banner image for advertisement" 
    )
    ad_url = models.URLField(
        blank=True,
        help_text="URL for ad banner to link to"
    )
    
    # SEO fields
    meta_title = models.CharField(
        max_length=60, 
        blank=True, 
        help_text="SEO Title (60 characters max)"
    )
    meta_description = models.CharField(
        max_length=160, 
        blank=True, 
        help_text="SEO Description (160 characters max)"
    )
    meta_keywords = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="Comma-separated keywords"
    )

    class Meta:
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog:blog_detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        # Generate slug if not provided
        if not self.slug:
            self.slug = slugify(self.title)
            
        # Auto-set publish date when status changes to published
        if self.status == "published" and not self.published_at:
            self.published_at = timezone.now()
            
        super().save(*args, **kwargs)

    # Image handling methods
    def get_main_image_url(self):
        """Get the URL for the main image"""
        if self.external_image_url:
            return self.external_image_url
        if self.featured_image:
            return self.featured_image.url
        return None

    def get_thumbnail_url(self):
        """Get the thumbnail URL - falls back to main image if no thumbnail"""
        if self.thumbnail:
            return self.thumbnail.url
        return self.get_main_image_url()

    def get_youtube_video_id(self):
        """Extract YouTube video ID from URL"""
        if not self.youtube_url:
            return None

        if "youtu.be" in self.youtube_url:
            return self.youtube_url.split("/")[-1]
        elif "v=" in self.youtube_url:
            return self.youtube_url.split("v=")[1].split("&")[0]
        return None

    def get_youtube_embed_url(self):
        """Get YouTube video embed URL"""
        video_id = self.get_youtube_video_id()
        if video_id:
            return f"https://www.youtube.com/embed/{video_id}"
        return None
        
    def get_youtube_thumbnail(self):
        """Get YouTube video thumbnail URL"""
        video_id = self.get_youtube_video_id()
        if video_id:
            return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        return None
        
    def get_ad_image_url(self):
        """Get the URL for the advertisement image"""
        if self.ad_image:
            return self.ad_image.url
        return None
    
    @property
    def is_published(self):
        """Check if post is published"""
        return self.status == "published"
    