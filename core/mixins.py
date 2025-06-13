# core/mixins.py
from django.conf import settings
import re


class MediaURLMixin:
    """
    Mixin to ensure media URLs are properly serialized as absolute URLs
    """

    def to_representation(self, instance):
        """Override to process media URLs in the serialized data"""
        data = super().to_representation(instance)
        return self.process_media_urls_in_data(data)

    def process_media_urls_in_data(self, data):
        """
        Recursively process data to convert relative media URLs to absolute URLs
        """
        if isinstance(data, dict):
            return {
                key: self.process_media_urls_in_data(value)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self.process_media_urls_in_data(item) for item in data]
        elif isinstance(data, str):
            return self.convert_media_urls(data)
        else:
            return data

    def convert_media_urls(self, content):
        """
        Convert relative media URLs to absolute URLs in content
        """
        if not content:
            return content

        # Base URL for the site
        base_url = getattr(settings, "SITE_URL", "https://corrison.corrisonapi.com")

        # Pattern to match media URLs
        patterns = [
            r'(/media/[^"\s]+)',  # /media/path/to/file
            r'(media/[^"\s]+)',  # media/path/to/file (without leading slash)
        ]

        for pattern in patterns:

            def replace_url(match):
                url = match.group(1)
                if not url.startswith("/media/"):
                    url = "/media/" + url.lstrip("media/")
                return f"{base_url}{url}"

            content = re.sub(pattern, replace_url, content)

        return content


class ImageFieldMixin:
    """
    Mixin to ensure ImageField URLs are properly converted to absolute URLs
    """

    def get_image_url(self, obj, field_name):
        """
        Get absolute URL for an image field
        """
        image_field = getattr(obj, field_name, None)
        if not image_field:
            return None

        try:
            url = image_field.url
            if url.startswith("http"):
                return url

            base_url = getattr(settings, "SITE_URL", "https://corrison.corrisonapi.com")
            return f"{base_url}{url}"
        except (ValueError, AttributeError):
            return None
