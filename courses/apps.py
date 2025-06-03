from django.apps import AppConfig


class CoursesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "courses"
    verbose_name = "Courses & Learning Management"

    def ready(self):
        """Import signals when app is ready"""
        try:
            import courses.signals
        except ImportError:
            pass
