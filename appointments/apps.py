# appointments/apps.py
from django.apps import AppConfig


class AppointmentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "appointments"
    verbose_name = "Calendar & Booking System"

    def ready(self):
        """Import signals when app is ready"""
        try:
            import appointments.signals
        except ImportError:
            pass
