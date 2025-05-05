# pages/views.py
from rest_framework import viewsets
from .models import Page
from .serializers import PageSerializer

class PageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Expose only published pages, lookup by slug.
    """
    queryset = Page.objects.filter(is_published=True)
    serializer_class = PageSerializer
    lookup_field = 'slug'
