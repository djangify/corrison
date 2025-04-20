# checkout/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Order, OrderItem, Address, Payment
from .services.checkout import CheckoutService, OrderService
from cart.services.cart_manager import CartService
import stripe
import json


def checkout(request):
    """
    Main checkout view.
    """
    # Get cart data
    cart_data = CartService.get_cart_data(request)
    
    # Check if cart is empty
    if cart_data['item_count'] == 0:
        messages.warning(request, 'Your cart is empty. Please add some items before checking out.')
        return redirect('cart:cart')
    
    # For logged in users, get their addresses
    addresses = None
    if request.user.is_authenticated:
        addresses = Address.objects.filter(user=request.user)
    
    context = {
        'cart': cart_data['cart'],
        'items': cart_data['items'],
        'subtotal': cart_data['subtotal'],
        'item_count': cart_data['item_count'],
        'addresses': addresses,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    }
    
    return render(request, 'checkout/checkout.html', context)


def process_checkout(request):
    """
    Process the checkout form.
    """
    if request.method != 'POST':
        return redirect('checkout:checkout')
    
    # Get cart data
    cart_data = CartService.get_cart_data(request)
    
    # Check if cart is empty
    if cart_data['item_count'] == 0:
        messages.warning(request, 'Your cart is empty. Please add some items before checking out.')
        return redirect('cart:cart')
    
    # Get form data
    form_data = request.POST
    
    # Create address objects (or get existing ones for authenticated users)
    billing_data = {
        'full_name': form_data.get('billing_name'),
        'address_line1': form_data.get('billing_address1'),
        'address_line2': form_data.get('billing_address2', ''),
        'city': form_data.get('billing_city'),
        'state_province': form_data.get('billing_state'),
        'postal_code': form_data.get('billing_zip'),
        'country': form_data.get('billing_country'),
        'phone': form_data.get('billing_phone'),
    }
    
    # Check if shipping address is same as billing
    if form_data.get('same_as_billing'):
        shipping_data = billing_data
    else:
        shipping_data = {
            'full_name': form_data.get('shipping_name'),
            'address_line1': form_data.get('shipping_address1'),
            'address_line2': form_data.get('shipping_address2', ''),
            'city': form_data.get('shipping_city'),
            'state_province': form_data.get('shipping_state'),
            'postal_code': form_data.get('shipping_zip'),
            'country': form_data.get('shipping_country'),
            'phone': form_data.get('shipping_phone'),
        }
    
    # Additional order data
    order_data = {
        'email': request.user.email if request.user.is_authenticated else form_data.get('email'),
        'shipping_method': form_data.get('shipping_method', 'standard'),
        'notes': form_data.get('order_notes', ''),
        'payment_method': form_data.get('payment_method', 'stripe'),
    }
    
    # Create the order
    success, order, error_message = CheckoutService.create_order_from_cart(
        request,
        billing_address=billing_data,
        shipping_address=shipping_data,
        **order_data
    )
    
    if not success:
        messages.error(request, error_message or 'An error occurred while processing your order.')
        return redirect('checkout:checkout')
    
    # If payment method is stripe, create payment intent
    if order_data['payment_method'] == 'stripe':
        # Create a payment intent
        success, client_secret, error_message = CheckoutService.create_payment_intent(
            order, payment_method='stripe'
        )
        
        if not success:
            messages.error(request, error_message or 'An error occurred with the payment processor.')
            return redirect('checkout:checkout')
        
        # Store the client secret in the session
        request.session['payment_intent_client_secret'] = client_secret
        request.session['order_id'] = str(order.id)
        
        # Redirect to payment page
        return redirect('checkout:payment')
    
    # For other payment methods (COD, bank transfer, etc.)
    # Since these don't require online payment, we can redirect to confirmation
    return redirect('checkout:confirmation', order_number=order.order_number)


def payment(request):
    """
    Payment page view.
    """
    # Check if we have a payment intent client secret in the session
    client_secret = request.session.get('payment_intent_client_secret')
    order_id = request.session.get('order_id')
    
    if not client_secret or not order_id:
        messages.error(request, 'Payment session expired. Please try again.')
        return redirect('checkout:checkout')
    
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        messages.error(request, 'Order not found. Please try again.')
        return redirect('checkout:checkout')
    
    context = {
        'client_secret': client_secret,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        'order': order,
    }
    
    return render(request, 'checkout/payment.html', context)


@csrf_exempt
def stripe_webhook(request):
    """
    Stripe webhook handler.
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    success, order, error_message = CheckoutService.handle_stripe_webhook(payload, sig_header)
    
    if not success:
        return HttpResponse(status=400)
    
    return HttpResponse(status=200)


def payment_success(request):
    """
    Payment success view.
    """
    # Get order from session
    order_id = request.session.get('order_id')
    
    if not order_id:
        messages.error(request, 'Order not found. Please try again.')
        return redirect('checkout:checkout')
    
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        messages.error(request, 'Order not found. Please try again.')
        return redirect('checkout:checkout')
    
    # Update order status if it hasn't been updated by webhook
    if order.payment_status == 'pending':
        order.payment_status = 'paid'
        order.status = 'processing'
        order.save()
    
    # Clear session data
    if 'payment_intent_client_secret' in request.session:
        del request.session['payment_intent_client_secret']
    if 'order_id' in request.session:
        del request.session['order_id']
    
    # Redirect to confirmation page
    return redirect('checkout:confirmation', order_number=order.order_number)


def confirmation(request, order_number):
    """
    Order confirmation view.
    """
    order = get_object_or_404(Order, order_number=order_number)
    
    # Security check: only the user who placed the order or a guest with the matching session ID can view it
    if request.user.is_authenticated:
        if order.user and order.user != request.user:
            messages.error(request, 'You do not have permission to view this order.')
            return redirect('core:home')
    else:
        # For guest users, check if the order is in the session
        if request.session.get('order_id') != str(order.id):
            messages.error(request, 'You do not have permission to view this order.')
            return redirect('core:home')
    
    context = {
        'order': order,
        'items': order.items.all(),
    }
    
    return render(request, 'checkout/confirmation.html', context)


@login_required
def order_detail(request, order_number):
    """
    Order detail view.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    context = {
        'order': order,
        'items': order.items.all(),
    }
    
    return render(request, 'checkout/order_detail.html', context)


@login_required
def order_list(request):
    """
    Order list view.
    """
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    
    return render(request, 'checkout/order_list.html', context)


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
    return redirect('checkout:order_detail', order_number=order_number)
