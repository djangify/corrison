# checkout/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .models import Order, OrderItem, OrderSettings
from .services.checkout import CheckoutService, OrderService
from cart.services.cart_manager import CartService
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .serializers import OrderSettingsSerializer
import stripe


def get_cart_token_from_request(request):
    """
    Get cart token from request - simplified.
    """
    # Try Authorization header first
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]

    # Try from session
    cart_token = request.session.get("cart_token")
    if cart_token:
        return cart_token

    # Try from POST data
    if request.method == "POST":
        cart_token = request.POST.get("cart_token")
        if cart_token:
            return cart_token

    # Try from GET parameters
    cart_token = request.GET.get("cart_token")
    if cart_token:
        return cart_token

    return None


def checkout(request):
    """
    Digital-only checkout view.
    """
    # Get cart token and cart data
    cart_token = get_cart_token_from_request(request)
    cart_data = CartService.get_cart_data(request, cart_token)

    # Check if cart is empty
    if cart_data["item_count"] == 0:
        messages.warning(
            request, "Your cart is empty. Please add some items before checking out."
        )
        return redirect("products:catalog")

    # Store cart token in session for checkout process
    if cart_data.get("cart_token"):
        request.session["cart_token"] = cart_data["cart_token"]

    context = {
        "cart": cart_data["cart"],
        "items": cart_data["items"],
        "subtotal": cart_data["subtotal"],
        "item_count": cart_data["item_count"],
        "cart_token": cart_data["cart_token"],
        "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
        # Digital-only flags
        "is_digital_only": True,
        "requires_shipping": False,
        "has_digital_items": True,
        "has_physical_items": False,
    }

    return render(request, "checkout/checkout.html", context)


def process_checkout(request):
    """
    Process digital-only checkout.
    """
    if request.method != "POST":
        return redirect("checkout:checkout")

    # Get cart token and cart data
    cart_token = get_cart_token_from_request(request)
    cart_data = CartService.get_cart_data(request, cart_token)

    # Check if cart is empty
    if cart_data["item_count"] == 0:
        messages.warning(
            request, "Your cart is empty. Please add some items before checking out."
        )
        return redirect("products:catalog")

    # Get form data
    form_data = request.POST

    # Digital-only order data - no shipping needed
    order_data = {
        "email": request.user.email
        if request.user.is_authenticated
        else form_data.get("email"),
        "notes": form_data.get("order_notes", ""),
        "payment_method": form_data.get("payment_method", "stripe"),
        "digital_delivery_email": form_data.get("digital_email")
        or (
            request.user.email
            if request.user.is_authenticated
            else form_data.get("email")
        ),
        "cart_token": cart_data.get("cart_token"),
    }

    # Create the order from cart
    success, order, error_message = CheckoutService.create_order_from_cart(
        request, **order_data
    )

    if not success:
        messages.error(
            request, error_message or "An error occurred while processing your order."
        )
        return redirect("checkout:checkout")

    # Create payment intent for Stripe
    if order_data["payment_method"] == "stripe":
        success, client_secret, error_message = CheckoutService.create_payment_intent(
            order, payment_method="stripe"
        )

        if not success:
            messages.error(
                request,
                error_message or "An error occurred with the payment processor.",
            )
            return redirect("checkout:checkout")

        # Store the client secret in the session
        request.session["payment_intent_client_secret"] = client_secret
        request.session["order_id"] = order.id

        # Redirect to payment page
        return redirect("checkout:payment")

    # For other payment methods
    return redirect("checkout:confirmation", order_number=order.order_number)


def payment(request):
    """
    Digital-only payment page.
    """
    # Check if we have a payment intent client secret in the session
    client_secret = request.session.get("payment_intent_client_secret")
    order_id = request.session.get("order_id")

    if not client_secret or not order_id:
        messages.error(request, "Payment session expired. Please try again.")
        return redirect("checkout:checkout")

    # Get the order
    order = get_object_or_404(Order, id=order_id)

    context = {
        "order": order,
        "client_secret": client_secret,
        "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
        "is_digital_only": True,
    }

    return render(request, "checkout/payment.html", context)


@csrf_exempt
def stripe_webhook(request):
    """
    Handle Stripe webhooks for digital product delivery.
    """
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    # Handle successful payment
    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]

        # Find the order and mark as paid
        try:
            order = Order.objects.get(stripe_payment_intent_id=payment_intent["id"])
            order.payment_status = "paid"
            order.status = "completed"  # Digital orders complete immediately
            order.save()

            # Clear the cart since order is complete
            if order.cart_token:
                CartService.clear_cart(order.cart_token)

            # Send digital delivery email
            OrderService.send_digital_delivery_email(order)

        except Order.DoesNotExist:
            pass

    return HttpResponse(status=200)


def confirmation(request, order_number):
    """
    Digital-only order confirmation.
    """
    order = get_object_or_404(Order, order_number=order_number)

    # Security check
    if request.user.is_authenticated:
        if order.user and order.user != request.user:
            messages.error(request, "You do not have permission to view this order.")
            return redirect("products:catalog")
    else:
        if request.session.get("order_id") != order.id:
            messages.error(request, "You do not have permission to view this order.")
            return redirect("products:catalog")

    # Get digital download items
    digital_items = order.items.filter(is_digital=True)

    context = {
        "order": order,
        "items": order.items.all(),
        "digital_items": digital_items,
        "is_digital_only": True,
    }

    return render(request, "checkout/confirmation.html", context)


@login_required
def order_detail(request, order_number):
    """
    Digital-only order detail view.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    # Get digital download items
    digital_items = order.items.filter(is_digital=True)

    context = {
        "order": order,
        "items": order.items.all(),
        "digital_items": digital_items,
        "is_digital_only": True,
    }

    return render(request, "checkout/order_detail.html", context)


@login_required
def order_list(request):
    """
    Digital-only order list view.
    """
    orders = Order.objects.filter(user=request.user).order_by("-created_at")

    context = {
        "orders": orders,
    }

    return render(request, "checkout/order_list.html", context)


def digital_download(request, download_token):
    """
    Handle digital product downloads.
    """
    # Get the order item by download token
    order_item = get_object_or_404(
        OrderItem, download_token=download_token, is_digital=True
    )

    # Check if user has permission to download
    if request.user.is_authenticated:
        if order_item.order.user and order_item.order.user != request.user:
            messages.error(request, "You do not have permission to download this file.")
            return redirect("products:catalog")
    else:
        # For guest orders, you might want additional verification
        pass

    # Check if download is still valid
    if not order_item.can_download:
        messages.error(request, "This download is no longer available.")
        return redirect("products:catalog")

    # Serve the file
    return OrderService.serve_digital_download(order_item)


class OrderSettingsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for order page settings.
    """

    serializer_class = OrderSettingsSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return OrderSettings.objects.all()
