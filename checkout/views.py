# checkout/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
from .models import Order, Payment
from api.serializers import OrderSerializer, PaymentSerializer
import stripe
import logging
from .models import OrderSettings
from .serializers import OrderSettingsSerializer

logger = logging.getLogger(__name__)

# Set Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY


class OrderViewSet(viewsets.ModelViewSet):
    """
    Orders: authenticated users only - digital-only focus.
    """

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
@permission_classes([AllowAny])  # Allow anonymous checkout
def create_payment_intent(request):
    """
    Create Stripe payment intent for digital products.
    No shipping address needed.
    """
    try:
        from cart.services.cart_manager import CartService

        # Get cart data
        cart_token = request.headers.get("Authorization", "").replace("Bearer ", "")
        cart_data = CartService.get_cart_data(request, cart_token)

        if cart_data["item_count"] == 0:
            return Response(
                {"error": "Cart is empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get customer data from request
        customer_email = request.data.get("email", "")
        notes = request.data.get("notes", "")

        # Create payment intent for digital products
        intent = stripe.PaymentIntent.create(
            amount=int(cart_data["subtotal"] * 100),  # Convert to cents
            currency="usd",
            automatic_payment_methods={
                "enabled": True,
                "allow_redirects": "never",  # Disable redirect-based payment methods
            },
            metadata={
                "cart_token": cart_data["cart_token"],
                "item_count": cart_data["item_count"],
                "is_digital_only": "true",
                "customer_notes": notes[:500] if notes else "",  # Limit notes length
            },
            receipt_email=customer_email if customer_email else None,
            description=f"Digital products order ({cart_data['item_count']} items)",
        )

        logger.info(
            f"Payment intent created: {intent.id} for cart {cart_data['cart_token']}"
        )

        return Response(
            {
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id,
            }
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        return Response(
            {"error": "Payment processing error. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    except Exception as e:
        logger.error(f"Payment intent creation error: {str(e)}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def check_payment_status(request):
    """
    Check payment status by payment intent ID.
    Used for order confirmation page.
    """
    payment_intent_id = request.GET.get("payment_intent")

    if not payment_intent_id:
        return Response(
            {"error": "Payment intent ID required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Retrieve payment intent from Stripe
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        # Check if order exists
        order = None
        try:
            order = Order.objects.get(stripe_payment_intent_id=payment_intent_id)
            order_data = OrderSerializer(order).data
        except Order.DoesNotExist:
            order_data = None

        return Response(
            {
                "payment_status": intent.status,
                "payment_amount": intent.amount / 100,  # Convert from cents
                "order": order_data,
                "success": intent.status == "succeeded",
            }
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error checking payment status: {str(e)}")
        return Response(
            {"error": "Unable to check payment status"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class OrderSettingsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for order settings - read-only access for all users
    """

    queryset = OrderSettings.objects.all()
    serializer_class = OrderSettingsSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        """Always return the first (and only) OrderSettings instance"""
        obj, created = OrderSettings.objects.get_or_create(pk=1)
        return obj
