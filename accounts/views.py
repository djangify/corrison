# accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Profile, WishlistItem
from products.models import Product
from django.core.paginator import Paginator
from checkout.models import Order


def register(request):
    """
    User registration view.
    """
    if request.user.is_authenticated:
        return redirect('core:home')
        
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        # Validate data
        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/register.html')
            
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'accounts/register.html')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'accounts/register.html')
            
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Create user profile
        Profile.objects.create(user=user)
        
        # Log in the user
        login(request, user)
        messages.success(request, 'Registration successful! Welcome to Corrison.')
        
        return redirect('core:home')
    
    return render(request, 'accounts/register.html')


def login_view(request):
    """
    User login view.
    """
    if request.user.is_authenticated:
        return redirect('core:home')
        
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Redirect to next page if provided
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
                
            return redirect('core:home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    """
    User logout view.
    """
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('core:home')


@login_required
def profile(request):
    """
    User profile view.
    """
    profile = request.user.profile
    
    if request.method == 'POST':
        # Update profile
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        birth_date = request.POST.get('birth_date') or None
        
        # Update user
        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.email = email
        request.user.save()
        
        # Update profile
        profile.phone = phone
        profile.birth_date = birth_date
        
        # Update preferences
        profile.email_marketing = 'email_marketing' in request.POST
        profile.receive_order_updates = 'receive_order_updates' in request.POST
        profile.save()
        
        messages.success(request, 'Profile updated successfully.')
    
    context = {
        'profile': profile
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
def change_password(request):
    """
    Change password view.
    """
    if request.method == 'POST':
        # Get form data
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validate data
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            return render(request, 'accounts/change_password.html')
            
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return render(request, 'accounts/change_password.html')
            
        # Update password
        request.user.set_password(new_password)
        request.user.save()
        
        # Re-authenticate the user
        user = authenticate(request, username=request.user.username, password=new_password)
        login(request, user)
        
        messages.success(request, 'Password changed successfully.')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/change_password.html')


@login_required
def order_history(request):
    """
    Order history view.
    """
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Paginate orders
    paginator = Paginator(orders, 10)
    page = request.GET.get('page')
    orders_page = paginator.get_page(page)
    
    context = {
        'orders': orders_page
    }
    
    return render(request, 'accounts/order_history.html', context)


@login_required
def order_detail(request, order_number):
    """
    Order detail view.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    context = {
        'order': order
    }
    
    return render(request, 'accounts/order_detail.html', context)


@login_required
def wishlist(request):
    """
    User wishlist view.
    """
    wishlist_items = WishlistItem.objects.filter(user=request.user).select_related('product')
    
    context = {
        'wishlist_items': wishlist_items
    }
    
    return render(request, 'accounts/wishlist.html', context)


@login_required
def add_to_wishlist(request, product_id):
    """
    Add product to wishlist.
    """
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    # Check if product is already in wishlist
    if WishlistItem.objects.filter(user=request.user, product=product).exists():
        messages.info(request, f"{product.name} is already in your wishlist.")
    else:
        # Add to wishlist
        WishlistItem.objects.create(user=request.user, product=product)
        messages.success(request, f"{product.name} added to your wishlist.")
    
    # Redirect back to product page or stay on current page
    next_url = request.GET.get('next') or reverse('products:product_detail', args=[product.slug])
    return redirect(next_url)


@login_required
def remove_from_wishlist(request, item_id):
    """
    Remove product from wishlist.
    """
    wishlist_item = get_object_or_404(WishlistItem, id=item_id, user=request.user)
    product_name = wishlist_item.product.name
    wishlist_item.delete()
    
    messages.success(request, f"{product_name} removed from your wishlist.")
    
    # Redirect back to wishlist
    return redirect('accounts:wishlist')
