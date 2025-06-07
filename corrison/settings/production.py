import os
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# ALLOWED_HOSTS
ALLOWED_HOSTS = [
    "corrison.corrisonapi.com",
    "corrisonapi.com",
    "ecommerce.corrisonapi.com",
    ".corrisonapi.com",
    "mail.corrisonapi.com",
    "65.108.89.200",
    "localhost",
    "127.0.0.1",
]

# Database in base.py is already set up to use environment variables

# CORS Configuration
# Since you're using AllowedOrigin model, we need to ensure CORS middleware can access it
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = []  # Empty because we're using the signal-based approach with AllowedOrigin model
CORS_ALLOW_ALL_ORIGINS = True  # before changing this back to false create a new ecommerce store that is not on the signal list and see if you can connect

# Headers that should be exposed
CORS_EXPOSE_HEADERS = [
    "Content-Type",
    "X-CSRFToken",
    "Set-Cookie",
]

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "https://corrison.corrisonapi.com",
    "https://ecommerce.corrisonapi.com",
    "https://corrisonapi.com",
]


# CSRF Configuration
CSRF_TRUSTED_ORIGINS = [
    "https://corrison.corrisonapi.com",
    "https://corrisonapi.com",
    "https://ecommerce.corrisonapi.com",
    "https://65.108.89.200",
    "http://localhost",
    "http://127.0.0.1",
]

# CSRF Cookie Configuration
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "None"  # Required for cross-site requests
CSRF_COOKIE_HTTPONLY = False  # Frontend needs to read this

# Session Configuration
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_NAME = "corrison_sessionid"  # Add unique name
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = False  # Change from True to False to allow JS access
SESSION_COOKIE_SAMESITE = "None"  # Already set correctly
SESSION_COOKIE_DOMAIN = ".corrisonapi.com"  # Add this to share across subdomains
SESSION_COOKIE_PATH = "/"  # Add this
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 1 week
SESSION_SAVE_EVERY_REQUEST = True

# Security settings
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Email settings for production
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@corrisonapi.com")

# Logging Configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs/django-error.log"),
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "cors_file": {  # Add this handler
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs/cors-debug.log"),
            "maxBytes": 10485760,
            "backupCount": 3,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file", "console"],
            "level": "ERROR",
            "propagate": True,
        },
        "core": {  # Add this logger
            "handlers": ["cors_file", "console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
# Ensure logs directory exists
log_dir = os.path.join(BASE_DIR, "logs")
os.makedirs(log_dir, exist_ok=True)

# Load site-specific settings
# try:
#     from .site_settings import *
# except ImportError:
#     pass


# Email verification settings
EMAIL_VERIFICATION_URL = "https://corrison.corrisonapi.com/auth/verify-email"
EMAIL_VERIFICATION_TOKEN_EXPIRY = 36  # hours
SITE_NAME = "Corrison"
