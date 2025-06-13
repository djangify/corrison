# core/templatetags/media_tags.py
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
import re

register = template.Library()


@register.filter
def process_media_urls(content):
    """
    Process content to convert relative media URLs to absolute URLs
    and ensure proper media file serving
    """
    if not content:
        return content

    # Pattern to match media URLs in content
    # Matches both /media/ and media/ patterns
    media_pattern = r'(?:src="|href=")(?:/?media/[^"]+)"'

    def replace_media_url(match):
        url = match.group(0)
        # Extract the media path
        media_path = re.search(r'(/?media/[^"]+)', url).group(1)

        # Ensure it starts with /media/
        if not media_path.startswith("/media/"):
            media_path = "/media/" + media_path.lstrip("media/")

        # Create absolute URL
        base_url = getattr(settings, "SITE_URL", "https://corrison.corrisonapi.com")
        absolute_url = f"{base_url}{media_path}"

        # Replace the URL in the original match
        return url.replace(media_path, absolute_url)

    # Process the content
    processed_content = re.sub(media_pattern, replace_media_url, content)

    return mark_safe(processed_content)


@register.filter
def absolute_media_url(media_path):
    """
    Convert a media path to absolute URL
    Usage: {{ product.image|absolute_media_url }}
    """
    if not media_path:
        return ""

    # Handle ImageField objects
    if hasattr(media_path, "url"):
        media_path = media_path.url

    # Convert to string if it's not already
    media_path = str(media_path)

    # If it's already absolute, return as-is
    if media_path.startswith("http"):
        return media_path

    # Ensure it starts with /media/
    if not media_path.startswith("/media/"):
        if media_path.startswith("media/"):
            media_path = "/" + media_path
        else:
            media_path = "/media/" + media_path

    # Create absolute URL
    base_url = getattr(settings, "SITE_URL", "https://corrison.corrisonapi.com")
    return f"{base_url}{media_path}"
