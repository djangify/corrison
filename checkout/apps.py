# checkout/apps.py
from django.apps import AppConfig


class CheckoutConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "checkout"

    def ready(self):
        """Import signals when app is ready"""
        try:
            import checkout.signals  # noqa: F401
        except ImportError:
            pass
