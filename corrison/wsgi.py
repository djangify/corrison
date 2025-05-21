import os

from django.core.wsgi import get_wsgi_application

# Set the default settings module for production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'corrison.settings.production')

application = get_wsgi_application()