from django.apps import AppConfig

class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        from .models import AllowedOrigin
        from corsheaders.signals import check_request_enabled
        from django.dispatch import receiver

        @receiver(check_request_enabled)
        def cors_allow_if_whitelisted(sender, request, **kwargs):
            origin = request.META.get('HTTP_ORIGIN')
            if origin and AllowedOrigin.objects.filter(origin=origin).exists():
                return True