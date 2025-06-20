# api/views.py
from django.contrib.auth import get_user_model
from rest_framework import viewsets, filters
from django.views.decorators.csrf import csrf_exempt
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


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def create_payment_intent(request):
    """
    Handle Stripe payment intent creation for digital products.
    Now includes inline user registration for new users.
    """
    try:
        import stripe
        from django.conf import settings
        from cart.models import Cart, CartItem
        from accounts.models import Profile
        from accounts.utils import send_verification_email
        from django.db import transaction

        print(f"\n=== PAYMENT INTENT REQUEST ===")
        print(f"User: {request.user}, Authenticated: {request.user.is_authenticated}")
        print(f"Session key: {request.session.session_key}")

        # Check if user is authenticated via Django session OR JWT
        user = None
        if request.user and request.user.is_authenticated:
            print(f"Session authenticated user detected: {request.user.email}")
            user = request.user
        else:
            # Check for JWT authentication
            from rest_framework_simplejwt.authentication import JWTAuthentication

            try:
                jwt_auth = JWTAuthentication()
                validated_token = jwt_auth.get_validated_token(
                    jwt_auth.get_raw_token(request)
                )
                jwt_user = jwt_auth.get_user(validated_token)
                if jwt_user and jwt_user.is_authenticated:
                    print(f"JWT authenticated user detected: {jwt_user.email}")
                    user = jwt_user
            except Exception as e:
                print(f"No JWT authentication found: {e}")

        if user:
            # Use the authenticated user's information
            email = user.email
            first_name = user.first_name
            last_name = user.last_name

            # Get cart directly for authenticated user
            cart = Cart.objects.filter(user=user, is_active=True).first()

            print(
                f"Cart lookup result: Cart ID {cart.id if cart else 'None'}, Items: {cart.items.count() if cart else 0}"
            )

            # NEW: If no user cart or cart is empty, check for session cart
            if not cart or cart.items.count() == 0:
                session_key = request.session.session_key
                if session_key:
                    session_cart = Cart.objects.filter(
                        session_key=session_key, is_active=True
                    ).first()

                    if session_cart and session_cart.items.exists():
                        if not cart:
                            # No user cart exists, just use session cart and assign user
                            session_cart.user = user
                            session_cart.save()
                            cart = session_cart
                        else:
                            # User cart exists but is empty, merge session cart into it
                            cart.merge_with(session_cart)

            # Re-check cart after potential merge
            if not cart:
                # Try one more time to get the user's cart after merge
                cart = Cart.objects.filter(user=user, is_active=True).first()

            if not cart or cart.items.count() == 0:
                print(
                    f"Cart empty after merge. Cart: {cart}, Items: {cart.items.count() if cart else 0}"
                )
                return Response(
                    {"error": "Cart is empty"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Set Stripe API key
            stripe.api_key = settings.STRIPE_SECRET_KEY

            # Create payment intent metadata for authenticated user
            metadata = {
                "session_key": request.session.session_key or "",
                "item_count": str(cart.items.count()),
                "is_digital_only": "true",
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "user_id": str(user.id),
                "authenticated_user": "true",
                "cart_id": str(cart.id),  # Add cart ID for webhook processing
            }

            # Debug the amount calculation
            cart_subtotal_float = float(cart.subtotal)
            stripe_amount = int(cart_subtotal_float * 100)

            print(f"=== STRIPE AMOUNT DEBUG (Authenticated) ===")
            print(f"Cart subtotal: {cart.subtotal}")
            print(f"Cart subtotal (float): {cart_subtotal_float}")
            print(f"Stripe amount (cents): {stripe_amount}")
            print(f"Expected dollars: ${stripe_amount / 100}")
            print(f"=========================")

            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=stripe_amount,  # Use the calculated amount
                currency="usd",
                metadata=metadata,
            )

            # RETURN HERE FOR AUTHENTICATED USERS - THIS IS THE FIX!
            return Response(
                {
                    "client_secret": intent.client_secret,
                    "payment_intent_id": intent.id,
                    "authenticated": True,
                    "email": email,
                }
            )

        # ===== GUEST CHECKOUT SECTION - ONLY RUNS IF NOT AUTHENTICATED =====

        # Get cart for anonymous users
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        cart = Cart.objects.filter(session_key=session_key, is_active=True).first()

        print(f"Cart for guest checkout: {cart}")
        print(f"Session key: {session_key}")

        if not cart or cart.items.count() == 0:
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
            # User exists but not logged in - they should log in
            return Response(
                {
                    "error": "An account already exists with this email. Please log in to complete your purchase."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
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

                    # Transfer cart from anonymous session to new user
                    if session_key:
                        # Get the anonymous cart
                        anon_cart = Cart.objects.filter(
                            session_key=session_key, is_active=True
                        ).first()

                        if anon_cart:
                            # Transfer items to user's cart
                            user_cart, created = Cart.objects.get_or_create(
                                user=user, is_active=True, defaults={"is_active": True}
                            )

                            # Move all items
                            for item in anon_cart.items.all():
                                CartItem.objects.update_or_create(
                                    cart=user_cart,
                                    product=item.product,
                                    defaults={"quantity": item.quantity},
                                )

                            # Delete anonymous cart
                            anon_cart.delete()

                            # CRITICAL: Use the user's cart for the rest of the process
                            cart = user_cart

        # Set Stripe API key
        stripe.api_key = settings.STRIPE_SECRET_KEY

        # Create payment intent metadata
        metadata = {
            "session_key": session_key,
            "item_count": str(cart.items.count()),
            "is_digital_only": "true",
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "cart_id": str(cart.id),
        }

        if user:
            metadata["user_id"] = str(user.id)
            metadata["new_user"] = "true"

        # Debug the cart and amount calculation
        print(f"=== CART DEBUG ===")
        print(f"Cart exists: {cart is not None}")
        print(f"Cart ID: {cart.id if cart else 'No cart'}")
        print(f"Cart items count: {cart.items.count() if cart else 0}")
        print(f"Cart is_active: {cart.is_active if cart else 'N/A'}")

        # Debug each item
        if cart and cart.items.exists():
            for item in cart.items.all():
                print(
                    f"Item: {item.product.name} - Price: {item.unit_price} - Qty: {item.quantity} - Total: {item.total_price}"
                )

        cart_subtotal_decimal = cart.subtotal if cart else 0
        cart_subtotal_float = float(cart_subtotal_decimal)
        stripe_amount = int(cart_subtotal_float * 100)

        print(f"=== STRIPE AMOUNT DEBUG ===")
        print(f"Cart subtotal (Decimal): {cart_subtotal_decimal}")
        print(f"Cart subtotal (float): {cart_subtotal_float}")
        print(f"Stripe amount (cents): {stripe_amount}")
        print(f"Expected dollars: ${stripe_amount / 100}")
        print(f"=========================")

        # Create payment intent for digital products (no shipping)
        intent = stripe.PaymentIntent.create(
            amount=stripe_amount,  # Use the calculated amount
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
        print(f"Error in create_payment_intent: {str(e)}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def create_order(request):
    """
    Handle digital-only order creation after successful payment.
    Orders now require authenticated users - no guest checkout.
    """
    logger.info(f"=== CREATE ORDER CALLED ===")
    logger.info(f"User: {request.user}")
    logger.info(f"Is authenticated: {request.user.is_authenticated}")
    logger.info(f"Session key: {request.session.session_key}")
    logger.info(f"Payment intent ID: {request.data.get('payment_intent_id')}")

    # KEEP ALL THE EXISTING CODE BELOW THIS
    logger.info("=== Starting create_order ===")
    logger.info(f"Request data: {request.data}")

    try:
        from checkout.services.checkout import CheckoutService
        from django.db import transaction
        from checkout.models import Payment
        from cart.models import Cart

        # Get payment intent ID
        payment_intent_id = request.data.get("payment_intent_id")
        if not payment_intent_id:
            logger.error("No payment_intent_id provided")
            return Response(
                {"error": "Payment intent ID is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(f"Payment intent ID: {payment_intent_id}")

        # Verify payment with Stripe
        import stripe
        from django.conf import settings

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

        # Get user from payment intent metadata or current user
        user = None
        user_id = payment_intent.metadata.get("user_id")

        logger.info(f"User ID from metadata: {user_id}")
        logger.info(f"Authenticated user: {request.user.is_authenticated}")

        if user_id:
            try:
                user = User.objects.get(id=user_id)
                logger.info(f"Found user from metadata: {user.email}")
            except User.DoesNotExist:
                logger.error(f"User with ID {user_id} not found")

        if not user and request.user.is_authenticated:
            user = request.user
            logger.info(f"Using authenticated user: {user.email}")

        if not user:
            # Try to get user by email from metadata
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

        # Get the cart for this user
        logger.info(f"Looking for cart for user: {user.email}")

        # First try to get cart by user
        cart = Cart.objects.filter(user=user, is_active=True).first()

        # NEW: If no user cart or cart is empty, check for session cart
        if not cart or cart.items.count() == 0:
            session_key = request.session.session_key
            if session_key:
                session_cart = Cart.objects.filter(
                    session_key=session_key, is_active=True
                ).first()

                if session_cart and session_cart.items.exists():
                    if not cart:
                        # No user cart exists, just use session cart and assign user
                        session_cart.user = user
                        session_cart.save()
                        cart = session_cart
                    else:
                        # User cart exists but is empty, merge session cart into it
                        cart.merge_with(session_cart)

        if not cart or cart.items.count() == 0:
            return Response(
                {"error": "Cart is empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # If no user cart, try session cart
        if not cart:
            session_key = (
                payment_intent.metadata.get("session_key")
                or request.session.session_key
            )
            if session_key:
                logger.info(f"Looking for session cart with key: {session_key}")
                cart = Cart.objects.filter(
                    session_key=session_key, is_active=True
                ).first()

        if not cart:
            logger.error(f"No active cart found for user {user.email}")
            return Response(
                {"error": "No active cart found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(f"Found cart: {cart.id} with {cart.items.count()} items")

        # Verify cart has items
        if cart.items.count() == 0:
            logger.error("Cart is empty")
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
            "stripe_payment_intent_id": payment_intent_id,
        }

        logger.info(f"Order data: {order_data}")

        # Create the order with user
        with transaction.atomic():
            try:
                # Create a mock request with the correct user
                class MockRequest:
                    def __init__(self, user, session):
                        self.user = user
                        self.session = session

                mock_request = MockRequest(user, request.session)

                logger.info("Calling CheckoutService.create_order_from_cart...")
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
                logger.info("Creating payment record...")
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

                # Process successful payment (sends emails, marks as complete if digital-only)
                logger.info("Processing successful payment...")
                CheckoutService.process_successful_payment(order)

                # Verify digital products were set up
                for item in order.items.filter(is_digital=True):
                    if not item.download_token:
                        logger.warning(f"No download token for digital item {item.id}")
                    else:
                        logger.info(
                            f"Download token created for item {item.id}: {item.download_token}"
                        )

            except Exception as e:
                logger.error(
                    f"Error during order creation transaction: {str(e)}", exc_info=True
                )
                raise

        # Serialize the order
        logger.info("Serializing order response...")
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

        logger.info(
            f"Order creation completed successfully for order {order.order_number}"
        )
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
