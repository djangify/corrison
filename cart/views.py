# cart/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from products.models import Product, ProductVariant
from .models import Cart, CartItem
from .services.cart_manager import CartService
import json


def cart_view(request):
    """
    View for displaying the shopping cart.
    """
    # Get cart data
    cart_data = CartService.get_cart_data(request)
    
    context = {
        'cart': cart_data['cart'],
        'items': cart_data['items'],
        'subtotal': cart_data['subtotal'],
        'item_count': cart_data['item_count']
    }
    
    return render(request, 'cart/cart.html', context)


def add_to_cart(request):
    """
    View for adding a product to the cart.
    """
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        variant_id = request.POST.get('variant_id')
        
        # Validate quantity
        if quantity < 1:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Quantity must be at least 1.'
                })
            messages.error(request, 'Quantity must be at least 1.')
            return redirect('products:product_detail', slug=request.POST.get('product_slug'))
        
        # Add to cart using CartService
        success, message, cart_item = CartService.add_to_cart(
            request, product_id, quantity, variant_id
        )
        
        if success:
            # For AJAX requests
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # Get updated cart data
                cart_data = CartService.get_cart_data(request)
                
                return JsonResponse({
                    'status': 'success',
                    'message': message,
                    'cart_count': cart_data['item_count'],
                    'cart_total': cart_data['subtotal']
                })
            
            messages.success(request, message)
            
            # Redirect back to product page or specified next URL
            next_url = request.POST.get('next') or 'cart:cart'
            return redirect(next_url)
        else:
            # For AJAX requests
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': message
                })
            
            messages.error(request, message)
            
            # Redirect back to product page or specified next URL
            next_url = request.POST.get('next') or 'cart:cart'
            return redirect(next_url)
    
    # Redirect to cart for non-POST requests
    return redirect('cart:cart')


def update_cart(request):
    """
    View for updating cart items.
    """
    if request.method == 'POST':
        try:
            # For AJAX requests, get data from request body
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                data = json.loads(request.body)
                item_id = data.get('item_id')
                quantity = int(data.get('quantity', 0))
            else:
                item_id = request.POST.get('item_id')
                quantity = int(request.POST.get('quantity', 0))
            
            # Update cart using CartService
            success, message = CartService.update_cart_item(request, item_id, quantity)
            
            if success:
                # Get updated cart data
                cart_data = CartService.get_cart_data(request)
                
                # For AJAX requests
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'message': message,
                        'cart_count': cart_data['item_count'],
                        'cart_total': cart_data['subtotal']
                    })
                
                messages.success(request, message)
            else:
                # For AJAX requests
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'message': message
                    })
                
                messages.error(request, message)
            
        except (ValueError, TypeError):
            # For AJAX requests
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid quantity.'
                })
            
            messages.error(request, 'Invalid quantity.')
    
    # Redirect to cart
    return redirect('cart:cart')


def remove_from_cart(request, item_id):
    """
    View for removing an item from the cart.
    """
    # Remove from cart using CartService
    success, message = CartService.remove_from_cart(request, item_id)
    
    if success:
        # For AJAX requests
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Get updated cart data
            cart_data = CartService.get_cart_data(request)
            
            return JsonResponse({
                'status': 'success',
                'message': message,
                'cart_count': cart_data['item_count'],
                'cart_total': cart_data['subtotal']
            })
        
        messages.success(request, message)
    else:
        # For AJAX requests
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': message
            })
        
        messages.error(request, message)
    
    # Redirect to cart
    return redirect('cart:cart')


def clear_cart(request):
    """
    View for clearing all items from the cart.
    """
    # Clear cart using CartService
    success, message = CartService.clear_cart(request)
    
    if success:
        # For AJAX requests
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': message,
                'cart_count': 0,
                'cart_total': 0
            })
        
        messages.success(request, message)
    else:
        # For AJAX requests
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': 'An error occurred while clearing your cart.'
            })
        
        messages.error(request, 'An error occurred while clearing your cart.')
    
    # Redirect to cart
    return redirect('cart:cart')


def mini_cart(request):
    """
    View for displaying the mini cart (used in AJAX requests).
    """
    # Get cart data
    cart_data = CartService.get_cart_data(request)
    
    context = {
        'cart': cart_data['cart'],
        'items': cart_data['items'],
        'subtotal': cart_data['subtotal'],
        'item_count': cart_data['item_count']
    }
    
    return render(request, 'cart/partials/mini_cart.html', context)
