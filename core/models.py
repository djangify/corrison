from django.db import models
from django.utils.text import slugify
import uuid

class TimestampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    created_at and updated_at fields.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """
    An abstract base class model that provides a UUID id field.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class SluggedModel(models.Model):
    """
    An abstract base class model that provides a slug field that is automatically
    populated from the name field.
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class PublishableModel(models.Model):
    """
    An abstract base class model that provides is_active field for
    enabling/disabling records.
    """
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class SEOModel(models.Model):
    """
    An abstract base class model that provides SEO fields.
    """
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        abstract = True


class ContactMessage(UUIDModel, TimestampedModel):
    """
    Model for storing contact form messages from users.
    """
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_read']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Message from {self.name} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"