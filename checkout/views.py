# checkout/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Order, OrderItem, Payment
from .services.checkout import CheckoutService, OrderService
from cart.services.cart_manager import CartService
import stripe
import json


def get_cart_token_from_request(request):
    """
    Helper function to get cart token from various sources.
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
    Main checkout view.
    """
    # Get cart token and cart data
    cart_token = get_cart_token_from_request(request)
    cart_data = CartService.get_cart_data(request, cart_token)

    # Check if cart is empty
    if cart_data["item_count"] == 0:
        messages.warning(
            request, "Your cart is empty. Please add some items before checking out."
        )
        return redirect("products:catalog")  # Redirect to catalog instead of cart:cart

    # Store cart token in session for checkout process
    if cart_data.get("cart_token"):
        request.session["cart_token"] = cart_data["cart_token"]

    # Check if cart contains only digital items
    cart = cart_data.get("cart")
    is_digital_only = cart_data.get("is_digital_only", False)

    context = {
        "cart": cart_data["cart"],
        "items": cart_data["items"],
        "subtotal": cart_data["subtotal"],
        "item_count": cart_data["item_count"],
        "cart_token": cart_data["cart_token"],
        "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
        "is_digital_only": is_digital_only,
        "requires_shipping": cart_data.get("requires_shipping", True),
        "has_digital_items": cart_data.get("has_digital_items", False),
        "has_physical_items": cart_data.get("has_physical_items", False),
    }

    return render(request, "checkout/checkout.html", context)


def process_checkout(request):
    """
    Process the checkout form.
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

    # Check if cart contains only digital items
    is_digital_only = cart_data.get("is_digital_only", False)

    # Order data - no addresses needed, Stripe collects them
    order_data = {
        "email": request.user.email
        if request.user.is_authenticated
        else form_data.get("email"),
        "shipping_method": form_data.get("shipping_method", "standard")
        if not is_digital_only
        else None,
        "notes": form_data.get("order_notes", ""),
        "payment_method": form_data.get("payment_method", "stripe"),
        "digital_delivery_email": form_data.get("digital_email")
        if is_digital_only
        else None,
        "cart_token": cart_data.get("cart_token"),  # Pass cart token
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

    # If payment method is stripe, create payment intent
    if order_data["payment_method"] == "stripe":
        # Create a payment intent
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

    # For other payment methods (COD, bank transfer, etc.)
    return redirect("checkout:confirmation", order_number=order.order_number)


def payment(request):
    """
    Payment page view.
    """
    # Check if we have a payment intent client secret in the session
    client_secret = request.session.get("payment_intent_client_secret")
    order_id = request.session.get("order_id")

    if not client_secret or not order_id:
        messages.error(request, "Payment session expired. Please try again.")
        return redirect("checkout:checkout")

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        messages.error(request, "Order not found. Please try again.")
        return redirect("checkout:checkout")

    context = {
        "client_secret": client_secret,
        "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
        "order": order,
    }

    return render(request, "checkout/payment.html", context)


@csrf_exempt
def stripe_webhook(request):
    """
    Stripe webhook handler.
    """
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    success, order, error_message = CheckoutService.handle_stripe_webhook(
        payload, sig_header
    )

    if not success:
        return HttpResponse(status=400)

    return HttpResponse(status=200)


def payment_success(request):
    """
    Payment success view.
    """
    # Get order from session
    order_id = request.session.get("order_id")

    if not order_id:
        messages.error(request, "Order not found. Please try again.")
        return redirect("checkout:checkout")

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        messages.error(request, "Order not found. Please try again.")
        return redirect("checkout:checkout")

    # Update order status if it hasn't been updated by webhook
    if order.payment_status == "pending":
        order.payment_status = "paid"
        order.status = "processing"
        order.save()

    # Clear session data
    if "payment_intent_client_secret" in request.session:
        del request.session["payment_intent_client_secret"]
    if "order_id" in request.session:
        del request.session["order_id"]
    if "cart_token" in request.session:
        del request.session["cart_token"]

    # Redirect to confirmation page
    return redirect("checkout:confirmation", order_number=order.order_number)


def confirmation(request, order_number):
    """
    Order confirmation view.
    """
    order = get_object_or_404(Order, order_number=order_number)

    # Security check: only the user who placed the order or a guest with the matching session ID can view it
    if request.user.is_authenticated:
        if order.user and order.user != request.user:
            messages.error(request, "You do not have permission to view this order.")
            return redirect("products:catalog")
    else:
        # For guest users, check if the order is in the session
        if request.session.get("order_id") != order.id:
            messages.error(request, "You do not have permission to view this order.")
            return redirect("products:catalog")

    # Get digital download items for the confirmation page
    digital_items = order.items.filter(is_digital=True)

    context = {
        "order": order,
        "items": order.items.all(),
        "digital_items": digital_items,
        "has_digital_items": order.has_digital_items,
        "has_physical_items": order.has_physical_items,
    }

    return render(request, "checkout/confirmation.html", context)


@login_required
def order_detail(request, order_number):
    """
    Order detail view.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    # Get digital download items
    digital_items = order.items.filter(is_digital=True)

    context = {
        "order": order,
        "items": order.items.all(),
        "digital_items": digital_items,
        "has_digital_items": order.has_digital_items,
        "has_physical_items": order.has_physical_items,
    }

    return render(request, "checkout/order_detail.html", context)


@login_required
def order_list(request):
    """
    Order list view.
    """
    orders = Order.objects.filter(user=request.user).order_by("-created_at")

    context = {
        "orders": orders,
    }

    return render(request, "checkout/order_list.html", context)


@login_required
@require_POST
def cancel_order(request, order_number):
    """
    Cancel order view.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    # Try to cancel the order
    success, message = OrderService.cancel_order(order)

    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)

    # Redirect back to order detail
    return redirect("checkout:order_detail", order_number=order_number)


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
        # For guest users, check if they have the order in session or provide order verification
        messages.error(request, "Please log in to download your files.")
        return redirect("accounts:login")

    # Check if download is still valid
    if not order_item.can_download:
        if order_item.download_count >= order_item.max_downloads:
            messages.error(request, "Download limit exceeded for this file.")
        else:
            messages.error(request, "Download link has expired.")
        return redirect(
            "checkout:order_detail", order_number=order_item.order.order_number
        )

    # Get the file to download
    download_file = order_item.get_download_file()

    if not download_file:
        messages.error(request, "Download file not found.")
        return redirect(
            "checkout:order_detail", order_number=order_item.order.order_number
        )

    # Increment download count
    order_item.download_count += 1
    order_item.save()

    # Serve the file
    from django.http import FileResponse
    import os

    try:
        response = FileResponse(
            open(download_file.path, "rb"),
            as_attachment=True,
            filename=os.path.basename(download_file.name),
        )
        return response
    except FileNotFoundError:
        messages.error(request, "Download file not found on server.")
        return redirect(
            "checkout:order_detail", order_number=order_item.order.order_number
        )
