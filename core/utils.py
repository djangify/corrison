# core/utils.py
import re
from django.conf import settings
from urllib.parse import urljoin


def process_content_media_urls(content):
    """
    Process HTML content to convert relative /media/ URLs to absolute URLs.

    This function finds image src attributes that start with '/media/' and
    converts them to full absolute URLs using the current site domain.

    Args:
        content (str): HTML content that may contain relative media URLs

    Returns:
        str: HTML content with absolute media URLs

    Example:
        Input:  '<img src="/media/products/image.jpg" alt="Product">'
        Output: '<img src="https://corrison.corrisonapi.com/media/products/image.jpg" alt="Product">'
    """
    if not content:
        return content

    # Get the base URL for the site
    # In production this will be your domain, in development it could be localhost
    if hasattr(settings, "SITE_URL"):
        base_url = settings.SITE_URL
    else:
        # Fallback - you may want to set SITE_URL in your settings
        base_url = "https://corrison.corrisonapi.com"

    # Pattern to match img src attributes with relative /media/ URLs
    # This will match: src="/media/..." or src='/media/...'
    pattern = r'src=["\'](/media/[^"\']+)["\']'

    def replace_url(match):
        relative_url = match.group(1)  # Extract the /media/... part
        absolute_url = urljoin(base_url, relative_url)
        quote_char = match.group(0)[4]  # Get the quote character (' or ")
        return f"src={quote_char}{absolute_url}{quote_char}"

    # Replace all relative media URLs with absolute URLs
    processed_content = re.sub(pattern, replace_url, content)

    return processed_content


def process_all_content_media_urls(content_dict):
    """
    Process multiple content fields in a dictionary to convert relative media URLs.

    This is useful when you have multiple content fields that need processing
    in a single serializer or model instance.

    Args:
        content_dict (dict): Dictionary with content fields as values

    Returns:
        dict: Dictionary with processed content fields

    Example:
        Input:  {'description': '<img src="/media/test.jpg">', 'content': '<img src="/media/other.jpg">'}
        Output: {'description': '<img src="https://domain.com/media/test.jpg">', 'content': '<img src="https://domain.com/media/other.jpg">'}
    """
    processed_dict = {}

    for key, content in content_dict.items():
        if isinstance(content, str):
            processed_dict[key] = process_content_media_urls(content)
        else:
            processed_dict[key] = content

    return processed_dict
