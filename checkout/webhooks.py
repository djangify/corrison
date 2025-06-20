# checkout/webhooks.py
import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from checkout.models import Order, Payment
from cart.models import Cart
from accounts.models import User
from courses.models import Enrollment
import logging

logger = logging.getLogger(__name__)

# Set Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Handle Stripe webhook events for digital product fulfillment.
    """
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        # Invalid payload
        logger.error("Invalid Stripe webhook payload")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        logger.error("Invalid Stripe webhook signature")
        return HttpResponse(status=400)

    # Handle the event
    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        handle_successful_payment(payment_intent)
    elif event["type"] == "payment_intent.payment_failed":
        payment_intent = event["data"]["object"]
        handle_failed_payment(payment_intent)
    else:
        logger.info(f"Unhandled Stripe event type: {event['type']}")

    return HttpResponse(status=200)


def handle_successful_payment(payment_intent):
    """
    Process successful payment and fulfill digital order.
    """
    logger.info(f"Processing successful payment: {payment_intent['id']}")

    try:
        # Get cart from metadata - try cart_id first, then cart_token for backwards compatibility
        cart_id = payment_intent.get("metadata", {}).get("cart_id")
        cart_token = payment_intent.get("metadata", {}).get("cart_token")

        if not cart_id and not cart_token:
            logger.error("No cart_id or cart_token in payment intent metadata")
            return

        # Find the cart
        try:
            if cart_id:
                cart = Cart.objects.get(id=cart_id)
            else:
                cart = Cart.objects.get(cart_token=cart_token)
        except Cart.DoesNotExist:
            logger.error(f"Cart not found for id: {cart_id} or token: {cart_token}")
            return

        # Get or create user from payment details
        email = payment_intent.get("receipt_email") or payment_intent.get(
            "charges", {}
        ).get("data", [{}])[0].get("billing_details", {}).get("email")

        # Also check metadata for email
        if not email:
            email = payment_intent.get("metadata", {}).get("email")

        if not email:
            logger.error("No email found in payment intent")
            return

        # Check if user_id is in metadata (for authenticated users)
        user_id = payment_intent.get("metadata", {}).get("user_id")

        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.error(f"User not found for id: {user_id}")
                return
        else:
            # Get or create user from email
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": email.split("@")[0],  # Simple username from email
                    "first_name": payment_intent.get("metadata", {}).get(
                        "first_name", ""
                    )
                    or payment_intent.get("charges", {})
                    .get("data", [{}])[0]
                    .get("billing_details", {})
                    .get("name", "")
                    .split()[0],
                    "last_name": payment_intent.get("metadata", {}).get("last_name", "")
                    or " ".join(
                        payment_intent.get("charges", {})
                        .get("data", [{}])[0]
                        .get("billing_details", {})
                        .get("name", "")
                        .split()[1:]
                    ),
                },
            )

        # Create order
        order = Order.objects.create(
            user=user,
            email=email,
            stripe_payment_intent_id=payment_intent["id"],
            payment_status="paid",
            order_status="completed",
            subtotal=payment_intent["amount"] / 100,  # Convert from cents
            total=payment_intent["amount"] / 100,
            order_type="digital",
        )

        # Create payment record
        Payment.objects.create(
            order=order,
            amount=payment_intent["amount"] / 100,
            stripe_payment_intent_id=payment_intent["id"],
            status="succeeded",
            payment_method="card",
        )

        # Process cart items for digital fulfillment
        for cart_item in cart.items.all():
            # Create order item
            order.items.create(
                product=cart_item.product,
                course=cart_item.course,
                quantity=cart_item.quantity,
                price=cart_item.unit_price,
                subtotal=cart_item.total_price,
            )

            # Handle course enrollments
            if cart_item.course:
                Enrollment.objects.get_or_create(
                    user=user,
                    course=cart_item.course,
                    defaults={
                        "payment_status": "paid",
                        "payment_amount": cart_item.total_price,
                        "stripe_payment_intent_id": payment_intent["id"],
                    },
                )
                logger.info(
                    f"Enrolled user {user.email} in course {cart_item.course.title}"
                )

            # For digital products, you might want to generate download links here
            if cart_item.product and cart_item.product.product_type == "digital":
                # TODO: Generate secure download link
                logger.info(
                    f"Digital product {cart_item.product.name} purchased by {user.email}"
                )

        # Clear the cart after successful order
        cart.items.all().delete()
        cart.is_active = False
        cart.save()  # This will update totals

        # TODO: Send order confirmation email with download links

        logger.info(f"Order {order.id} created successfully for {email}")

    except Exception as e:
        logger.error(
            f"Error processing payment intent {payment_intent['id']}: {str(e)}"
        )


def handle_failed_payment(payment_intent):
    """
    Handle failed payment attempts.
    """
    logger.warning(f"Payment failed: {payment_intent['id']}")

    # You might want to:
    # - Send a notification to the customer
    # - Update any pending order status
    # - Log the failure for analytics
