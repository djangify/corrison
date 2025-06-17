# api/views.py
from django.contrib.auth import get_user_model
from rest_framework import viewsets, filters
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
)
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
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
@permission_classes([AllowAny])
def check_email(request):
    """
    Check if an email already has an account
    """
    email = request.data.get("email", "").strip().lower()

    if not email:
        return Response(
            {"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Check if user exists with this email
    user_exists = User.objects.filter(email=email).exists()

    return Response({"exists": user_exists, "email": email})


@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])
def create_payment_intent(request):
    """
    Handle Stripe payment intent creation for digital products.
    Now includes inline user registration for new users.
    """
    try:
        import stripe
        from django.conf import settings
        from cart.services.cart_manager import CartService
        from accounts.models import Profile
        from accounts.utils import send_verification_email
        from django.db import transaction

        # Get cart data
        cart_token = request.data.get("cart_token") or request.headers.get(
            "Authorization", ""
        ).replace("Bearer ", "")
        cart_data = CartService.get_cart_data(request, cart_token)

        if cart_data["item_count"] == 0:
            return Response(
                {"error": "Cart is empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get customer data
        email = request.data.get("email", "").strip().lower()
        first_name = request.data.get("first_name", "").strip()
        last_name = request.data.get("last_name", "").strip()
        password = request.data.get("password", "")

        if not email:
            return Response(
                {"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not first_name:
            return Response(
                {"error": "First name is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user exists
        existing_user = User.objects.filter(email=email).first()

        if existing_user:
            # User exists - they should log in
            return Response(
                {
                    "error": "An account already exists with this email. Please log in to complete your purchase."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create new user if password provided
        user = None
        if password:
            with transaction.atomic():
                # Create username from email
                username = email.split("@")[0]
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1

                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )

                # Create profile (should be created by signal, but ensure it exists)
                profile, created = Profile.objects.get_or_create(user=user)

                # Generate verification token
                token = profile.generate_verification_token()

                # Send verification email
                try:
                    send_verification_email(user, token)
                except Exception as e:
                    print(f"Failed to send verification email: {e}")

        # Set Stripe API key
        stripe.api_key = settings.STRIPE_SECRET_KEY

        # Create payment intent metadata
        metadata = {
            "cart_token": cart_data["cart_token"],
            "item_count": cart_data["item_count"],
            "is_digital_only": "true",
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
        }

        if user:
            metadata["user_id"] = str(user.id)
            metadata["new_user"] = "true"

        # Create payment intent for digital products (no shipping)
        intent = stripe.PaymentIntent.create(
            amount=int(cart_data["subtotal"] * 100),  # Convert to cents
            currency="usd",
            metadata=metadata,
        )

        response_data = {
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id,
        }

        if user:
            response_data["user_created"] = True
            response_data["message"] = (
                "Account created successfully. You'll receive a verification email after purchase."
            )

        return Response(response_data)

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def create_order(request):
    """
    Handle digital-only order creation.
    Orders now require authenticated users - no guest checkout.
    """
    try:
        from checkout.services.checkout import CheckoutService
        from cart.services.cart_manager import CartService
        from django.db import transaction

        # Get payment intent ID
        payment_intent_id = request.data.get("payment_intent_id")
        if not payment_intent_id:
            return Response(
                {"error": "Payment intent ID is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify payment with Stripe
        import stripe
        from django.conf import settings

        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            if payment_intent.status != "succeeded":
                return Response(
                    {"error": "Payment not completed"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            return Response(
                {"error": f"Failed to verify payment: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get user from payment intent metadata or current user
        user = None
        user_id = payment_intent.metadata.get("user_id")

        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                pass

        if not user and request.user.is_authenticated:
            user = request.user

        if not user:
            return Response(
                {"error": "User account required for order creation"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get cart data
        cart_token = payment_intent.metadata.get("cart_token")
        if not cart_token:
            cart_token = request.headers.get("Authorization", "").replace("Bearer ", "")

        cart_data = CartService.get_cart_data(request, cart_token)

        if cart_data["item_count"] == 0:
            return Response(
                {"error": "Cart is empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Digital-only order data
        order_data = {
            "email": user.email,
            "notes": request.data.get("notes", ""),
            "payment_method": "stripe",
            "digital_delivery_email": user.email,
            "cart_token": cart_data["cart_token"],
        }

        # Create the order with user
        with transaction.atomic():
            # Override the request user for order creation
            request.user = user

            success, order, error_message = CheckoutService.create_order_from_cart(
                request, **order_data
            )

            if not success:
                return Response(
                    {"error": error_message or "Failed to create order"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Record the payment
            Payment.objects.create(
                order=order,
                payment_method="stripe",
                transaction_id=payment_intent_id,
                amount=order.total,
                status="completed",
                payment_data={"payment_intent": payment_intent_id},
            )

            # Update order payment status
            order.payment_status = "paid"
            order.status = "processing"
            order.save()

        # Serialize the order
        serializer = OrderSerializer(order, context={"request": request})

        response_data = {
            "order": serializer.data,
            "message": "Order created successfully",
            "success": True,
        }

        # Add verification reminder for new users
        if payment_intent.metadata.get("new_user") == "true":
            response_data["verification_required"] = True
            response_data["verification_message"] = (
                "Please check your email to verify your account and access your downloads."
            )

        return Response(response_data, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def check_payment_status(request):
    """
    Check the status of a payment intent
    """
    try:
        import stripe
        from django.conf import settings

        payment_intent_id = request.query_params.get("payment_intent")
        if not payment_intent_id:
            return Response(
                {"error": "Payment intent ID required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            # Check if order exists for this payment
            order = Order.objects.filter(
                payments__transaction_id=payment_intent_id
            ).first()

            response_data = {
                "success": payment_intent.status == "succeeded",
                "status": payment_intent.status,
            }

            if order:
                response_data["order"] = {
                    "id": str(order.id),
                    "order_number": order.order_number,
                    "total": float(order.total),
                }

            # Add verification reminder for new users
            if payment_intent.metadata.get("new_user") == "true":
                response_data["verification_required"] = True
                response_data["email"] = payment_intent.metadata.get("email")

            return Response(response_data)

        except Exception as e:
            return Response(
                {"error": f"Failed to check payment status: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
