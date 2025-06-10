# api/views.py
from django.contrib.auth import get_user_model
from rest_framework import viewsets, filters
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
)
from rest_framework.decorators import api_view
from rest_framework.viewsets import ReadOnlyModelViewSet

from products.models import Product, Category
from checkout.models import Order, Payment
from products.serializers import ProductSerializer
from .serializers import (
    OrderSerializer,
    PaymentSerializer,
    CategorySerializer,
)

User = get_user_model()


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for products.
    """

    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    lookup_field = "slug"
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description", "category__name"]
    ordering_fields = [
        "name",
        "price",
        "created_at",
    ]  # Removed "effective_price" - use model property instead

    def get_queryset(self):
        queryset = super().get_queryset()

        # REMOVED: effective_price annotation that was conflicting with model property
        # The Product model already has an effective_price property, so we don't need to annotate it

        # Add manual filtering
        category_slug = self.request.query_params.get("category", None)

        # Handle both naming conventions for price filters
        min_price = self.request.query_params.get(
            "min_price", None
        ) or self.request.query_params.get("price_gte", None)
        max_price = self.request.query_params.get(
            "max_price", None
        ) or self.request.query_params.get("price_lte", None)

        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        if min_price:
            queryset = queryset.filter(price__gte=min_price)

        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # Add prefetching to reduce DB queries
        return queryset.select_related("category").prefetch_related(
            "images", "variants"
        )


class CategoryViewSet(ReadOnlyModelViewSet):
    """
    A viewset for viewing categories.
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class OrderViewSet(viewsets.ModelViewSet):
    """
    Orders: authenticated users only.
    """

    # prefetch to pull in the items efficiently
    queryset = Order.objects.prefetch_related("items").all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class PaymentViewSet(viewsets.ModelViewSet):
    """
    Payments: authenticated users only.
    """

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(order__user=self.request.user)


# REMOVED: UserViewSet - Security fix
# User management is handled by dedicated auth endpoints:
# - auth/register/ (registration)
# - auth/login/ (login)
# - auth/profile/ (profile management)
# - auth/change-password/ (password changes)


# Custom API endpoints
@api_view(["POST"])
def add_to_cart(request):
    # Handle adding items to cart
    pass


@api_view(["PUT"])
def update_cart_item(request):
    # Handle updating cart item quantity
    pass


@api_view(["DELETE"])
def remove_cart_item(request):
    # Handle removing items from cart
    pass


@api_view(["POST"])
def create_payment_intent(request):
    # Handle Stripe payment intent creation
    pass


@api_view(["POST"])
def create_order(request):
    # Handle order creation
    pass


@api_view(["GET"])
def placeholder_image(request, width, height):
    # Generate placeholder images
    pass
