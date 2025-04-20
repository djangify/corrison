"""
Site-specific settings for the Corrison project.

This file contains settings that are specific to a particular deployment of the site.
Edit this file when deploying to a new domain.
"""
import os
from pathlib import Path

# Site information
SITE_NAME = "Corrison Store"
SITE_DOMAIN = "example.com"
SITE_LOGO = "images/logo.png"
CONTACT_EMAIL = "contact@example.com"
SUPPORT_PHONE = "+1 123-456-7890"

# Social media links
SOCIAL_LINKS = {
    "facebook": "https://facebook.com/corrison",
    "instagram": "https://instagram.com/corrison",
    "twitter": "https://twitter.com/corrison",
    "youtube": "https://youtube.com/corrison",
}

# Payment methods to enable
ENABLED_PAYMENT_METHODS = ["stripe", "paypal"]

# Theme settings
PRIMARY_COLOR = "#0d6efd"
SECONDARY_COLOR = "#6c757d"
ACCENT_COLOR = "#fd7e14"

# Typography
FONT_PRIMARY = "'Inter', sans-serif"
FONT_HEADINGS = "'Poppins', sans-serif"

# Analytics
GOOGLE_ANALYTICS_ID = ""

# Feature flags
ENABLE_WISHLIST = True
ENABLE_REVIEWS = True
ENABLE_NEWSLETTER = True
ENABLE_BLOG = True

# Product settings
PRODUCTS_PER_PAGE = 12
RELATED_PRODUCTS_LIMIT = 4
FEATURED_PRODUCTS_LIMIT = 8

# Shipping options
SHIPPING_METHODS = {
    "standard": {
        "name": "Standard Shipping",
        "price": 5.00,
        "description": "3-5 business days",
    },
    "express": {
        "name": "Express Shipping",
        "price": 15.00,
        "description": "1-2 business days",
    },
}

# Tax settings (e.g., flat rate of 10%)
TAX_RATE = 0.10

# Currency settings
CURRENCY_SYMBOL = "$"
CURRENCY_CODE = "USD"