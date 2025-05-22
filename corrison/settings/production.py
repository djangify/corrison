import os
import environ
from .base import *
import pymysql 

pymysql.install_as_MySQLdb()


# Read .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Updates to add to corrison/settings/production.py

# Make sure your domain is in ALLOWED_HOSTS
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['corrison.corrisonapi.com', 'corrisonapi.com', 'www.corrisonapi.com'])

# Make sure CSRF trusted origins include your domain
CSRF_TRUSTED_ORIGINS = env.list(
    'CSRF_TRUSTED_ORIGINS', 
    default=[
        'https://corrison.corrisonapi.com',
        'https://corrisonapi.com',
        'https://www.corrisonapi.com'
    ]
)

# Ensure your domain is listed in CORS allowed origins
CORS_ALLOWED_ORIGINS_APPEND = [
    'https://corrison.corrisonapi.com',
    'https://corrisonapi.com', 
    'https://www.corrisonapi.com'
]

# CORS settings - using the signal-based approach
# Note: Add your domains via the AllowedOrigin model in the admin interface
CORS_ALLOW_CREDENTIALS = True
CORS_EXPOSE_HEADERS = ['Content-Type', 'X-CSRFToken', 'Set-Cookie']
CORS_ALLOWED_ORIGINS = []       # keep empty to use signals
CORS_ALLOW_ALL_ORIGINS = False

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env("DATABASE_NAME"),
        "USER": env("DATABASE_USER"),
        "PASSWORD": env("DATABASE_PASSWORD"),
        "HOST": env("DATABASE_HOST", default="127.0.0.1"),
        "PORT": env("DATABASE_PORT", default="3306"),
        "CONN_MAX_AGE": 600,
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            "use_unicode": True,
            "connect_timeout": 10,
            "autocommit": True,
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
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'None'  # Keep as 'None' for cross-site requests
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'None'  # Keep as 'None' for cross-site requests

# Update CORS settings 
CORS_ALLOW_CREDENTIALS = True
CORS_EXPOSE_HEADERS = [
    'Content-Type',
    'X-CSRFToken',
    'Set-Cookie',
]

# Ensure your domains are in CSRF trusted origins
CSRF_TRUSTED_ORIGINS = [
    'https://corrison.corrisonapi.com',
    'https://corrisonapi.com',
    'https://www.corrisonapi.com',
    # Add any other frontend domains that need to make requests
]

# Session configuration
SESSION_SAVE_EVERY_REQUEST = True
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


# Configure logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/django-error.log'),
            'maxBytes': 10485760,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

# Ensure the logs directory exists with proper permissions
import os
log_dir = os.path.join(BASE_DIR, 'logs')
os.makedirs(log_dir, exist_ok=True)