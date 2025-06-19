from pathlib import Path
import os
import environ
from datetime import timedelta


# Initialize environment variables
env = environ.Env()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Read the .env file
env.read_env(os.path.join(BASE_DIR, ".env"))

# SECRET_KEY
SECRET_KEY = env("SECRET_KEY")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "tinymce",
    "django_filters",
    "accounts.apps.AccountsConfig",
    "api.apps.ApiConfig",
    "checkout.apps.CheckoutConfig",
    "core.apps.CoreConfig",
    "cart.apps.CartConfig",
    "products.apps.ProductsConfig",
    "blog.apps.BlogConfig",
    "pages.apps.PagesConfig",
    "linkhub.apps.LinkhubConfig",
    "appointments.apps.AppointmentsConfig",
    "courses.apps.CoursesConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "corrison.urls"

# CORS Configuration
# Since you're using AllowedOrigin model, we need to ensure CORS middleware can access it
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = []  # Empty because we're using the signal-based approach with AllowedOrigin model in django admin area
CORS_ALLOW_ALL_ORIGINS = True  # before changing this back to false create a new ecommerce store that is not on the signal list and see if you can connect

# Headers that should be exposed
CORS_EXPOSE_HEADERS = [
    "Content-Type",
    "X-CSRFToken",
    "Set-Cookie",
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
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


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "corrison.wsgi.application"

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Login URLs
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# Session settings (keeping minimal for admin only)
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 1 week
SESSION_SAVE_EVERY_REQUEST = True

CORS_SUPPORT_CREDENTIALS = True

# Stripe settings
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY", default="pk_test_placeholder")
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="sk_test_placeholder")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="whsec_placeholder")

# REST framework & JWT configuration
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",  # Keep for admin
    ],
}

# JWT Settings
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),  # Short-lived access tokens
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),  # 7-day refresh tokens
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}

# Email verification settings
EMAIL_VERIFICATION_TOKEN_EXPIRY = 24  # hours
ACCOUNT_EMAIL_VERIFICATION = "mandatory"

# Email settings for verification
EMAIL_VERIFICATION_URL = env(
    "EMAIL_VERIFICATION_URL", default="http://localhost:8000/api/v1/auth/verify-email"
)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@corrisonapi.com")

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DATABASE_NAME"),
        "USER": env("DATABASE_USER"),
        "PASSWORD": env("DATABASE_PASSWORD"),
        "HOST": env("DATABASE_HOST", default="localhost"),
        "PORT": env("DATABASE_PORT", default="5432"),
    }
}

# Appointments settings
CALENDAR_SETTINGS = {
    "DEFAULT_TIMEZONE": "UTC",
    "DEFAULT_BOOKING_WINDOW_DAYS": 30,
    "DEFAULT_BUFFER_MINUTES": 15,
    "MIN_APPOINTMENT_DURATION": 15,  # minutes
    "MAX_APPOINTMENT_DURATION": 480,  # 8 hours
    "ENABLE_EMAIL_NOTIFICATIONS": True,
    "ENABLE_SMS_NOTIFICATIONS": False,  # Future feature
}

# Courses settings
COURSES_SETTINGS = {
    "DEFAULT_COURSE_LANGUAGE": "English",
    "MAX_LESSONS_PER_COURSE": 100,
    "DEFAULT_LESSON_DURATION": 15,  # minutes
    "ENABLE_COURSE_CERTIFICATES": False,  # Future feature
    "ENABLE_COURSE_DISCUSSIONS": False,  # Future feature
}

# Email settings for appointments and courses notifications
if not hasattr(locals(), "SITE_URL"):
    SITE_URL = "https://corrisonapi.com"

# Django backend URL for media processing (where images are actually served)
DJANGO_BACKEND_URL = "https://corrison.corrisonapi.com"

# Site name for emails
SITE_NAME = "Corrison"

# Updated TinyMCE configuration for base.py
# Replace the existing TINYMCE_DEFAULT_CONFIG in your base.py with this:

TINYMCE_DEFAULT_CONFIG = {
    "height": 650,
    "width": "auto",
    "cleanup_on_startup": True,
    "custom_undo_redo_levels": 20,
    "selector": "textarea",
    "theme": "silver",
    "plugins": """
        textcolor save link image media preview codesample contextmenu
        table code lists fullscreen insertdatetime nonbreaking
        contextmenu directionality searchreplace wordcount visualblocks
        visualchars code fullscreen autolink lists charmap print hr
        anchor pagebreak
        """,
    "toolbar1": """
        fullscreen preview bold italic underline | fontselect,
        fontsizeselect | forecolor backcolor | alignleft alignright |
        aligncenter alignjustify | indent outdent | bullist numlist table |
        | link image media | codesample |
        """,
    "toolbar2": """
        visualblocks visualchars |
        charmap hr pagebreak nonbreaking anchor | code |
        """,
    "contextmenu": "formats | link image",
    "menubar": True,
    "statusbar": True,
    # MEDIA HANDLING CONFIGURATION
    "relative_urls": False,
    "remove_script_host": False,
    "convert_urls": True,
    "document_base_url": "https://corrison.corrisonapi.com/",
    # Image handling
    "automatic_uploads": True,
    "images_upload_url": "/admin/upload/",  # You may need to create this endpoint
    "images_upload_base_path": "/media/",
    "images_upload_credentials": True,
    # File handling
    "file_picker_types": "image media",
    "file_picker_callback": """
        function(callback, value, meta) {
            if (meta.filetype === 'image') {
                var input = document.createElement('input');
                input.setAttribute('type', 'file');
                input.setAttribute('accept', 'image/*');
                input.onchange = function() {
                    var file = this.files[0];
                    var reader = new FileReader();
                    reader.onload = function() {
                        callback(reader.result, {
                            alt: file.name
                        });
                    };
                    reader.readAsDataURL(file);
                };
                input.click();
            }
        }
    """,
}
