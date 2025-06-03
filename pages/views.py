# pages/views.py
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Page, Testimonial
from .serializers import PageSerializer, PageListSerializer, TestimonialSerializer


class PageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for pages with support for landing pages.

    Query parameters:
    - type: Filter by page type ('page' or 'landing')
    - category: Filter testimonials by category (when retrieving single page)
    """

    queryset = (
        Page.objects.filter(is_published=True)
        .select_related()
        .prefetch_related("features", "page_testimonials__testimonial")
    )
    lookup_field = "slug"
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["page_type"]
    search_fields = ["title", "content", "hero_title", "meta_description"]
    ordering_fields = ["order", "created_at", "updated_at", "title"]
    ordering = ["order", "-updated_at"]

    def get_serializer_class(self):
        """Use different serializers for list vs detail views"""
        if self.action == "list":
            return PageListSerializer
        return PageSerializer

    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = super().get_queryset()

        # Filter by page type if specified
        page_type = self.request.query_params.get("type", None)
        if page_type in ["page", "landing"]:
            queryset = queryset.filter(page_type=page_type)

        return queryset

    @action(detail=False, methods=["get"])
    def landing_pages(self, request):
        """Get all published landing pages"""
        landing_pages = self.get_queryset().filter(page_type="landing")

        page = self.paginate_queryset(landing_pages)
        if page is not None:
            serializer = PageListSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = PageListSerializer(
            landing_pages, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def regular_pages(self, request):
        """Get all published regular pages"""
        regular_pages = self.get_queryset().filter(page_type="page")

        page = self.paginate_queryset(regular_pages)
        if page is not None:
            serializer = PageListSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = PageListSerializer(
            regular_pages, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def testimonials(self, request, slug=None):
        """Get testimonials for a specific page, optionally filtered by category"""
        page = self.get_object()
        testimonials_qs = page.page_testimonials.all()

        # Filter by category if specified
        category = request.query_params.get("category", None)
        if category:
            testimonials_qs = testimonials_qs.filter(testimonial__category=category)

        testimonials_data = []
        for page_testimonial in testimonials_qs:
            testimonial_data = TestimonialSerializer(page_testimonial.testimonial).data
            testimonial_data["page_order"] = page_testimonial.order
            testimonials_data.append(testimonial_data)

        return Response(
            {
                "page": page.title,
                "testimonials": testimonials_data,
                "count": len(testimonials_data),
            }
        )


class TestimonialViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for testimonials.

    Query parameters:
    - category: Filter by category
    - featured: Filter featured testimonials (true/false)
    """

    queryset = Testimonial.objects.all()
    serializer_class = TestimonialSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["category", "is_featured", "rating"]
    search_fields = ["name", "company", "content", "title"]
    ordering_fields = ["order", "created_at", "name", "rating"]
    ordering = ["order", "-created_at"]

    @action(detail=False, methods=["get"])
    def featured(self, request):
        """Get all featured testimonials"""
        featured_testimonials = self.get_queryset().filter(is_featured=True)

        page = self.paginate_queryset(featured_testimonials)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(featured_testimonials, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def categories(self, request):
        """Get all testimonial categories"""
        categories = (
            self.get_queryset()
            .exclude(category="")
            .values_list("category", flat=True)
            .distinct()
            .order_by("category")
        )

        return Response({"categories": list(categories), "count": len(categories)})
