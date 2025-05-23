import os
import environ
from .base import *
import pymysql 

pymysql.install_as_MySQLdb()

# Read .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# ALLOWED_HOSTS
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[
    'corrison.corrisonapi.com', 
    'corrisonapi.com', 
    'www.corrisonapi.com',
    'localhost',  # for testing
])

# CORS Configuration 
# Since you're using AllowedOrigin model, we need to ensure CORS middleware can access it
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = []  # Empty because we're using the signal-based approach with AllowedOrigin model
CORS_ALLOW_ALL_ORIGINS = True #before changing this back to false create a new ecommerce store that is not on the signal list and see if you can connect

# Headers that should be exposed
CORS_EXPOSE_HEADERS = [
    'Content-Type',
    'X-CSRFToken',
    'Set-Cookie',
]

# CSRF Configuration
CSRF_TRUSTED_ORIGINS = [
    'https://corrison.corrisonapi.com',
    'https://corrisonapi.com',
    'https://www.corrisonapi.com',
    'https://ecommerce.corrisonapi.com',  # Add your frontend domain
    'http://ecommerce.corrisonapi.com',   # HTTP version too
]

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'None'  # Required for cross-site requests
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 1 week
SESSION_SAVE_EVERY_REQUEST = True

# CSRF Cookie Configuration
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'None'  # Required for cross-site requests
CSRF_COOKIE_HTTPONLY = False   # Frontend needs to read this

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
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
USE_X_FORWARDED_HOST = True

# Email settings for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@corrisonapi.com')

# Logging Configuration
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
        'cors_file': {  # Add this handler
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/cors-debug.log'),
            'maxBytes': 10485760,
            'backupCount': 3,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'core': {  # Add this logger
            'handlers': ['cors_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
# Ensure logs directory exists
log_dir = os.path.join(BASE_DIR, 'logs')
os.makedirs(log_dir, exist_ok=True)

# Load site-specific settings
try:
    from .site_settings import *
except ImportError:
    pass

# TEMPORARY DEBUG - Add this to see what's happening
# Remove this after fixing the issue
if DEBUG is False:
    import logging
    logger = logging.getLogger('django.request')
    logger.setLevel(logging.DEBUG)