"""
Production settings for the Corrison project.
"""
import os
import environ
from .base import *

# Read .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Read ALLOWED_HOSTS from environment or site_settings
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# Set CSRF trusted origins based on allowed hosts
CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS]
CSRF_TRUSTED_ORIGINS += [f"http://{host}" for host in ALLOWED_HOSTS]

# CORS origins from env
CORS_ALLOWED_ORIGINS = []       # use signal not static list
CORS_ALLOW_ALL_ORIGINS = False  

# Database settings for production
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DATABASE_NAME"),
        "USER": env("DATABASE_USER"),
        "PASSWORD": env("DATABASE_PASSWORD"),
        "HOST": env("DATABASE_HOST", default="db"),
        "PORT": env("DATABASE_PORT", default="5432"),  
        "CONN_MAX_AGE": 600,
        "OPTIONS": {
            "connect_timeout": 10,
        },
    },
}

# Security settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
USE_X_FORWARDED_HOST = True

# Session settings 
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_SECURE = True  # Keep this for HTTPS only
SESSION_COOKIE_SAMESITE = 'None'  # Changed from 'Lax' to 'None' for cross-domain
SESSION_COOKIE_HTTPONLY = True  
SESSION_COOKIE_DOMAIN = '.todiane.com'  # Allows sharing across subdomains

# CORS settings to expose the session headers
CORS_EXPOSE_HEADERS = [
    'Set-Cookie',
    'Cookie',
]

# ensure session cookies work with CORS
CORS_SUPPORT_CREDENTIALS = True   

# Session middleware configuration  
SESSION_SAVE_EVERY_REQUEST = True  

# Optional: increase session timeout if needed
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 1 week

# Email settings for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')


# Ensure logs directory exists
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# Load site-specific settings
try:
    from .site_settings import *
except ImportError:
    pass
