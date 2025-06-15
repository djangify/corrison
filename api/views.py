# api/views.py
from django.contrib.auth import get_user_model
from rest_framework import viewsets, filters
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
)
from rest_framework.decorators import api_view
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse

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
    API endpoint for products - digital-only focus.
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
    ]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Add manual filtering
        category_slug = self.request.query_params.get("category", None)
        product_type = self.request.query_params.get("product_type", None)

        # Handle both naming conventions for price filters
        min_price = self.request.query_params.get(
            "min_price", None
        ) or self.request.query_params.get("price_gte", None)
        max_price = self.request.query_params.get(
            "max_price", None
        ) or self.request.query_params.get("price_lte", None)

        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        # Filter by product type (useful for digital-only filtering)
        if product_type:
            queryset = queryset.filter(product_type=product_type)

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
    Orders: authenticated users only - digital-only focus.
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


@api_view(["POST"])
def create_payment_intent(request):
    """
    Handle Stripe payment intent creation for digital products.
    """
    try:
        import stripe
        from django.conf import settings
        from cart.services.cart_manager import CartService

        # Get cart data
        cart_token = request.headers.get("Authorization", "").replace("Bearer ", "")
        cart_data = CartService.get_cart_data(request, cart_token)

        if cart_data["item_count"] == 0:
            return Response(
                {"error": "Cart is empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Set Stripe API key
        stripe.api_key = settings.STRIPE_SECRET_KEY

        # Create payment intent for digital products (no shipping)
        intent = stripe.PaymentIntent.create(
            amount=int(cart_data["subtotal"] * 100),  # Convert to cents
            currency="usd",
            metadata={
                "cart_token": cart_data["cart_token"],
                "item_count": cart_data["item_count"],
                "is_digital_only": "true",
            },
        )

        return Response(
            {
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id,
            }
        )

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def create_order(request):
    """
    Handle digital-only order creation.
    """
    try:
        from checkout.services.checkout import CheckoutService
        from cart.services.cart_manager import CartService

        # Get cart data
        cart_token = request.headers.get("Authorization", "").replace("Bearer ", "")
        cart_data = CartService.get_cart_data(request, cart_token)

        if cart_data["item_count"] == 0:
            return Response(
                {"error": "Cart is empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get order data from request
        email = request.data.get("email")
        if request.user.is_authenticated:
            email = request.user.email
        elif not email:
            return Response(
                {"error": "Email is required for guest orders"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Digital-only order data
        order_data = {
            "email": email,
            "notes": request.data.get("notes", ""),
            "payment_method": "stripe",
            "digital_delivery_email": email,
            "cart_token": cart_data["cart_token"],
        }

        # Create the order
        success, order, error_message = CheckoutService.create_order_from_cart(
            request, **order_data
        )

        if not success:
            return Response(
                {"error": error_message or "Failed to create order"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Serialize the order
        serializer = OrderSerializer(order, context={"request": request})

        return Response(
            {
                "order": serializer.data,
                "message": "Order created successfully",
            },
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def placeholder_image(request, width, height):
    """
    Generate placeholder images dynamically.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        import io

        # Validate dimensions
        width = max(1, min(2000, int(width)))
        height = max(1, min(2000, int(height)))

        # Create image
        image = Image.new("RGB", (width, height), color="#e5e7eb")
        draw = ImageDraw.Draw(image)

        # Add text
        text = f"{width}×{height}"
        try:
            # Try to use a default font
            font = ImageFont.truetype("arial.ttf", size=min(width, height) // 10)
        except (OSError, IOError):
            # Fallback to default font
            font = ImageFont.load_default()

        # Calculate text position
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2

        # Draw text
        draw.text((x, y), text, fill="#6b7280", font=font)

        # Save to bytes
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        return HttpResponse(buffer.read(), content_type="image/png")

    except Exception:
        # Return a simple 1x1 pixel image on error
        image = Image.new("RGB", (1, 1), color="#e5e7eb")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return HttpResponse(buffer.read(), content_type="image/png")
