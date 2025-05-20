"""
Local development settings for the Corrison project.
"""
import os
import environ
from .base import *
from .base import env, BASE_DIR
import pymysql 

pymysql.install_as_MySQLdb()

# this will _overwrite_ any DATABASE_* etc already in os.environ
env.read_env(
    env_file=os.path.join(BASE_DIR, '.env_local'),
    override=True
)


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# CSRF settings for local development
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Allow requests from your frontend domain
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    # Add any other domains yo
    # u need
]

# These are the critical ones for cookies
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False  # Don't use this in production, but might help locally

# Session cookie settings
SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_SAMESITE = 'Lax'  # Try 'None' if 'Lax' doesn't work
SESSION_COOKIE_SECURE = False    # False for HTTP in development
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_PATH = '/'
SESSION_SAVE_EVERY_REQUEST = True  # Force session save on every request

# Add CORS headers explicitly
CORS_EXPOSE_HEADERS = [
    'Content-Type',
    'X-CSRFToken',
    'Set-Cookie',
]


# Debug settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Add this to help with debugging
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}

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



# Email settings for development (writes to console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# Load site-specific settings
try:
    from .site_settings import *
except ImportError:
    pass
