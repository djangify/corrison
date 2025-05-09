"""
Local development settings for the Corrison project.
"""
import os
import environ
from .base import *
import pymysql

# Read .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# CSRF settings for local development
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Allow requests from your frontend domain
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://ecommerce.todiane.com",
    # Add any other domains you need
]

pymysql.install_as_MySQLdb()
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env("DATABASE_NAME"),
        "USER": env("DATABASE_USER"),
        "PASSWORD": env("DATABASE_PASSWORD"),
        "HOST": env("DATABASE_HOST", default="127.0.0.1"),
        "PORT": env("DATABASE_PORT", default="3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
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
