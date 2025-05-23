from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        from .models import AllowedOrigin
        from corsheaders.signals import check_request_enabled
        from django.dispatch import receiver

        @receiver(check_request_enabled)
        def cors_allow_if_whitelisted(sender, request, **kwargs):
            origin = request.META.get('HTTP_ORIGIN')
            logger.info(f"CORS check - Origin: {origin}")
            
            if origin:
                try:
                    exists = AllowedOrigin.objects.filter(origin=origin).exists()
                    logger.info(f"CORS check - Origin {origin} exists: {exists}")
                    if exists:
                        return True
                except Exception as e:
                    logger.error(f"CORS check error: {e}")
            
            return None  # Let default CORS handling continue