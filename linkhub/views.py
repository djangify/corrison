# linkhub/views.py
from rest_framework import viewsets
from .models import LinkHub
from .serializers import LinkHubSerializer

class LinkHubViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Exposes GET /api/v1/linkhubs/ and /api/v1/linkhubs/{slug}/
    """
    queryset         = LinkHub.objects.prefetch_related('links')
    serializer_class = LinkHubSerializer
    lookup_field     = 'slug'
