# api/views.py
from django.contrib.auth import get_user_model
from rest_framework import viewsets, filters
from django.views.decorators.csrf import csrf_exempt
from cart.views import CartViewSet
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
)
import logging

from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from rest_framework.decorators import (
    api_view,
    permission_classes,
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

logger = logging.getLogger(__name__)


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
@csrf_exempt
def create_payment_intent(request):
    """
    Handle Stripe payment intent creation for digital products.
    Simplified cart handling with proper session/user cart resolution.
    """
    try:
        import stripe
        from django.conf import settings
        from accounts.models import Profile
        from accounts.utils import send_verification_email
        from django.db import transaction

        logger.info("\n=== PAYMENT INTENT REQUEST ===")
        logger.info(
            f"User: {request.user}, Authenticated: {request.user.is_authenticated}"
        )
        logger.info(f"Session key: {request.session.session_key}")

        # Ensure session exists
        if not request.session.session_key:
            request.session.create()

        session_key = request.session.session_key

        # Get the cart using the same logic as CartViewSet
        cart_viewset = CartViewSet()
        cart = cart_viewset.get_cart_from_request(request)

        logger.info(
            f"Cart found: ID {cart.id}, Items: {cart.items.count()}, User: {cart.user}"
        )

        if not cart or cart.items.count() == 0:
            return Response(
                {"error": "Cart is empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Set Stripe API key
        stripe.api_key = settings.STRIPE_SECRET_KEY

        # Handle authenticated users
        if request.user.is_authenticated:
            user = request.user
            email = user.email
            first_name = user.first_name
            last_name = user.last_name

            # Create payment intent metadata
            metadata = {
                "cart_id": str(cart.id),
                "user_id": str(user.id),
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "session_key": session_key,
                "authenticated_user": "true",
                "is_digital_only": "true",
                "item_count": str(cart.items.count()),
            }

            # Calculate amount
            cart_total = float(cart.total)
            stripe_amount = int(cart_total * 100)

            logger.info(
                f"Creating payment intent for authenticated user: ${cart_total}"
            )

            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=stripe_amount,
                currency="usd",
                metadata=metadata,
            )

            return Response(
                {
                    "client_secret": intent.client_secret,
                    "payment_intent_id": intent.id,
                    "authenticated": True,
                    "email": email,
                }
            )

        # Handle anonymous users
        email = request.data.get("email", "").strip().lower()
        first_name = request.data.get("first_name", "").strip()
        last_name = request.data.get("last_name", "").strip()
        password = request.data.get("password", "")

        # Validate required fields
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
            return Response(
                {
                    "error": "An account already exists with this email. Please log in to complete your purchase."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create new user if password provided
        new_user = None
        if password and len(password) >= 8:
            with transaction.atomic():
                # Generate unique username
                username = email.split("@")[0]
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1

                # Create user
                new_user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )

                # Create/ensure profile exists
                profile, created = Profile.objects.get_or_create(user=new_user)

                # Generate verification token
                token = profile.generate_verification_token()

                # Send verification email
                try:
                    send_verification_email(new_user, token)
                except Exception as e:
                    logger.error(f"Failed to send verification email: {e}")

                # Assign cart to new user
                cart.user = new_user
                cart.save(update_fields=["user", "updated_at"])

                logger.info(
                    f"Created new user {new_user.email} and assigned cart {cart.id}"
                )

        # Create payment intent metadata
        metadata = {
            "cart_id": str(cart.id),
            "session_key": session_key,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "is_digital_only": "true",
            "item_count": str(cart.items.count()),
        }

        if new_user:
            metadata["user_id"] = str(new_user.id)
            metadata["new_user"] = "true"

        # Calculate amount
        cart_total = float(cart.total)
        stripe_amount = int(cart_total * 100)

        logger.info(f"Creating payment intent for guest/new user: ${cart_total}")

        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=stripe_amount,
            currency="usd",
            metadata=metadata,
        )

        response_data = {
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id,
        }

        if new_user:
            response_data["user_created"] = True
            response_data["message"] = (
                "Account created successfully. You'll receive a verification email after purchase."
            )

        return Response(response_data)

    except Exception as e:
        logger.error(f"Error in create_payment_intent: {str(e)}", exc_info=True)
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def create_order(request):
    """
    Handle digital-only order creation after successful payment.
    Simplified cart and user resolution.
    """
    logger.info("=== CREATE ORDER CALLED ===")
    logger.info(f"User: {request.user}, Authenticated: {request.user.is_authenticated}")
    logger.info(f"Session key: {request.session.session_key}")
    logger.info(f"Request data: {request.data}")

    try:
        from checkout.services.checkout import CheckoutService
        from django.db import transaction
        from checkout.models import Payment
        from cart.models import Cart
        import stripe
        from django.conf import settings

        # Get payment intent ID
        payment_intent_id = request.data.get("payment_intent_id")
        if not payment_intent_id:
            logger.error("No payment_intent_id provided")
            return Response(
                {"error": "Payment intent ID is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify payment with Stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            logger.info("Retrieving payment intent from Stripe...")
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            logger.info(f"Payment intent status: {payment_intent.status}")
            logger.info(f"Payment intent metadata: {payment_intent.metadata}")

            if payment_intent.status != "succeeded":
                logger.error(f"Payment not completed. Status: {payment_intent.status}")
                return Response(
                    {"error": "Payment not completed"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            logger.error(
                f"Failed to verify payment with Stripe: {str(e)}", exc_info=True
            )
            return Response(
                {"error": f"Failed to verify payment: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get cart ID from payment intent metadata
        cart_id = payment_intent.metadata.get("cart_id")
        if not cart_id:
            logger.error("No cart_id in payment intent metadata")
            return Response(
                {"error": "Cart information missing from payment"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get the cart
        try:
            cart = Cart.objects.get(id=cart_id, is_active=True)
            logger.info(f"Found cart {cart.id} with {cart.items.count()} items")
        except Cart.DoesNotExist:
            logger.error(f"Cart {cart_id} not found")
            return Response(
                {"error": "Cart not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify cart has items
        if cart.items.count() == 0:
            logger.error("Cart is empty")
            return Response(
                {"error": "Cart is empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get or verify user
        user = None

        # First check if cart has a user
        if cart.user:
            user = cart.user
            logger.info(f"Using cart user: {user.email}")

        # Check authenticated user
        elif request.user.is_authenticated:
            user = request.user
            logger.info(f"Using authenticated user: {user.email}")

        # Check payment intent metadata
        else:
            user_id = payment_intent.metadata.get("user_id")
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    logger.info(f"Found user from metadata: {user.email}")
                except User.DoesNotExist:
                    logger.error(f"User {user_id} from metadata not found")

        # Last resort: find by email
        if not user:
            email = payment_intent.metadata.get("email")
            if email:
                try:
                    user = User.objects.get(email=email)
                    logger.info(f"Found user by email: {user.email}")
                except User.DoesNotExist:
                    logger.error(f"No user found with email: {email}")

        if not user:
            logger.error("No user found for order creation")
            return Response(
                {"error": "User account required for order creation"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Ensure cart is assigned to user
        if cart.user != user:
            cart.user = user
            cart.save(update_fields=["user"])

        # Prepare order data
        order_data = {
            "email": user.email,
            "notes": request.data.get("notes", ""),
            "payment_method": "stripe",
            "digital_delivery_email": user.email,
            "stripe_payment_intent_id": payment_intent_id,
        }

        logger.info(f"Creating order for user {user.email} with cart {cart.id}")

        # Create the order
        with transaction.atomic():
            try:
                # Create a request-like object with the user
                class MockRequest:
                    def __init__(self, user, session):
                        self.user = user
                        self.session = session

                mock_request = MockRequest(user, request.session)

                # Create order
                success, order, error_message = CheckoutService.create_order_from_cart(
                    mock_request, **order_data
                )

                if not success:
                    logger.error(f"CheckoutService failed: {error_message}")
                    return Response(
                        {"error": error_message or "Failed to create order"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                logger.info(f"Order created successfully: {order.order_number}")

                # Record the payment
                payment = Payment.objects.create(
                    order=order,
                    payment_method="stripe",
                    transaction_id=payment_intent_id,
                    amount=order.total,
                    status="completed",
                    payment_data={"payment_intent": payment_intent_id},
                )
                logger.info(f"Payment created: {payment.id}")

                # The Payment model's save() method will automatically:
                # 1. Update order payment status to 'paid'
                # 2. Set up digital downloads via setup_digital_product()
                # 3. Update order status

                # Process successful payment (sends emails, marks as complete)
                CheckoutService.process_successful_payment(order)

                # Verify digital products were set up
                digital_items_count = 0
                for item in order.items.filter(is_digital=True):
                    if item.download_token:
                        digital_items_count += 1
                        logger.info(f"Download token created for item {item.id}")
                    else:
                        logger.warning(f"No download token for digital item {item.id}")

                logger.info(f"Set up {digital_items_count} digital download(s)")

            except Exception as e:
                logger.error(f"Error during order creation: {str(e)}", exc_info=True)
                return Response(
                    {"error": f"Order creation failed: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        # Prepare response
        serializer = OrderSerializer(order, context={"request": request})

        response_data = {
            "order": serializer.data,
            "message": "Order created successfully",
            "success": True,
            "has_digital_items": order.has_digital_items,
            "email": user.email,
        }

        # Add verification reminder for new users
        if payment_intent.metadata.get("new_user") == "true":
            response_data["verification_required"] = True
            response_data["new_account_created"] = True

        logger.info(f"Order creation completed successfully: {order.order_number}")
        return Response(response_data, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Unexpected error in create_order: {str(e)}", exc_info=True)
        return Response(
            {"error": f"Order creation failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def check_payment_status(request):
    """
    Check the status of a payment intent and return order details
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
            order = (
                Order.objects.filter(payments__transaction_id=payment_intent_id)
                .select_related("user")
                .prefetch_related("items")
                .first()
            )

            response_data = {
                "success": payment_intent.status == "succeeded",
                "status": payment_intent.status,
            }

            if order:
                # Get the user's email (prefer order user over guest email)
                user_email = order.user.email if order.user else order.guest_email

                response_data["order"] = {
                    "id": str(order.id),
                    "order_number": order.order_number,
                    "total": float(order.total),
                    "guest_email": order.guest_email,
                    "has_digital_items": order.has_digital_items,
                    "items": [],
                }

                # Add email to response
                response_data["email"] = user_email

                # Include digital items with download info
                for item in order.items.all():
                    item_data = {
                        "id": item.id,
                        "product_name": item.product.name
                        if item.product
                        else item.product_snapshot.get("name", "Product"),
                        "quantity": item.quantity,
                        "price": float(item.price),
                        "is_digital": item.is_digital,
                    }

                    # Add download URL for digital items if user is authenticated
                    if (
                        item.is_digital
                        and item.download_token
                        and request.user.is_authenticated
                    ):
                        from django.urls import reverse

                        item_data["download_url"] = request.build_absolute_uri(
                            reverse(
                                "checkout:download-product",
                                kwargs={"token": item.download_token},
                            )
                        )

                    response_data["order"]["items"].append(item_data)

            # Add verification info from payment intent metadata
            if payment_intent.metadata.get("new_user") == "true":
                response_data["verification_required"] = True
                response_data["new_account_created"] = True
                response_data["email"] = payment_intent.metadata.get(
                    "email", response_data.get("email")
                )

            return Response(response_data)

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error checking payment status: {str(e)}")
            return Response(
                {"error": f"Failed to check payment status: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Exception as e:
        logger.error(f"Error in check_payment_status: {str(e)}", exc_info=True)
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
