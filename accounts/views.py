# accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from .models import Profile, WishlistItem
from .utils import (
    send_verification_email,
    send_password_reset_email,
    send_welcome_email,
)
from products.models import Product
from checkout.models import Order
from django.core.paginator import Paginator

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .serializers import WishlistItemSerializer


# =============================================================================
# WISHLIST VIEWS (Keep for now - may move to API later)
# =============================================================================


@login_required
def wishlist(request):
    """User wishlist view."""
    wishlist_items = WishlistItem.objects.filter(user=request.user).select_related(
        "product"
    )
    context = {"wishlist_items": wishlist_items}
    return render(request, "accounts/wishlist.html", context)


@login_required
def add_to_wishlist(request, product_id):
    """Add product to wishlist."""
    product = get_object_or_404(Product, id=product_id, is_active=True)

    # Check if product is already in wishlist
    if WishlistItem.objects.filter(user=request.user, product=product).exists():
        messages.info(request, f"{product.name} is already in your wishlist.")
    else:
        # Add to wishlist
        WishlistItem.objects.create(user=request.user, product=product)
        messages.success(request, f"{product.name} added to your wishlist.")

    # Redirect back to product page or stay on current page
    next_url = request.GET.get("next") or reverse(
        "products:product_detail", args=[product.slug]
    )
    return redirect(next_url)


@login_required
def remove_from_wishlist(request, item_id):
    """Remove product from wishlist."""
    wishlist_item = get_object_or_404(WishlistItem, id=item_id, user=request.user)
    product_name = wishlist_item.product.name
    wishlist_item.delete()

    messages.success(request, f"{product_name} removed from your wishlist.")
    return redirect("accounts:wishlist")


@login_required
def change_password(request):
    """Change password view."""
    if request.method == "POST":
        # Get form data
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        # Validate data
        if not request.user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
            return render(request, "accounts/change_password.html")

        if new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
            return render(request, "accounts/change_password.html")

        # Update password
        request.user.set_password(new_password)
        request.user.save()

        # Re-authenticate the user
        from django.contrib.auth import authenticate, login

        user = authenticate(
            request, username=request.user.username, password=new_password
        )
        login(request, user)

        messages.success(request, "Password changed successfully.")
        return redirect("accounts:profile")

    return render(request, "accounts/change_password.html")


@login_required
def order_history(request):
    """Order history view."""
    orders = Order.objects.filter(user=request.user).order_by("-created_at")

    # Paginate orders
    paginator = Paginator(orders, 10)
    page = request.GET.get("page")
    orders_page = paginator.get_page(page)

    context = {"orders": orders_page}
    return render(request, "accounts/order_history.html", context)


@login_required
def order_detail(request, order_number):
    """Order detail view."""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    context = {"order": order}
    return render(request, "accounts/order_detail.html", context)


# =============================================================================
# EMAIL VERIFICATION VIEWS (Django Templates)
# =============================================================================


def verify_email_page(request):
    """Show the 'check your email' page after registration."""
    email = request.GET.get("email", "")
    message = request.GET.get("message", "")

    context = {
        "email": email,
        "message": message,
    }
    return render(request, "accounts/verify_email.html", context)


def verify_email_token(request, token):
    """Handle email verification with token."""
    try:
        profile = Profile.objects.get(email_verification_token=token)

        # Check token expiry
        if profile.email_verification_sent_at:
            expiry_time = profile.email_verification_sent_at + timedelta(
                hours=getattr(settings, "EMAIL_VERIFICATION_TOKEN_EXPIRY", 24)
            )
            if timezone.now() > expiry_time:
                context = {
                    "status": "expired",
                    "error_message": "Verification token has expired. Please request a new one.",
                }
                return render(request, "accounts/verify_email_token.html", context)

        # Verify email
        profile.email_verified = True
        profile.email_verification_token = ""
        profile.email_verification_sent_at = None
        profile.save()

        # Send welcome email
        try:
            send_welcome_email(profile.user)
        except Exception as e:
            print(f"Failed to send welcome email: {e}")

        context = {"status": "success"}
        return render(request, "accounts/verify_email_token.html", context)

    except Profile.DoesNotExist:
        context = {"status": "error", "error_message": "Invalid verification token."}
        return render(request, "accounts/verify_email_token.html", context)


def resend_verification(request):
    """Resend verification email."""
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)
            profile = user.profile

            if profile.email_verified:
                return redirect(
                    f"/auth/verify-email/?email={email}&message=already_verified"
                )

            # Generate new token
            token = profile.generate_verification_token()

            # Send verification email
            send_verification_email(user, token)

            return redirect(f"/auth/verify-email/?email={email}&message=resent")

        except User.DoesNotExist:
            return redirect(f"/auth/verify-email/?email={email}&message=not_found")

    # Redirect to verify email page if not POST
    return redirect("/auth/verify-email/")


# =============================================================================
# PASSWORD RESET VIEWS (Django Templates)
# =============================================================================


def forgot_password(request):
    """Handle forgot password form."""
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)
            profile = user.profile

            # Generate password reset token
            reset_token = profile.generate_password_reset_token()

            # Send password reset email
            send_password_reset_email(user, reset_token)

            context = {
                "success": True,
                "email": email,
            }
            return render(request, "accounts/forgot_password.html", context)

        except User.DoesNotExist:
            context = {
                "error": "No account found with that email address.",
                "email": email,
            }
            return render(request, "accounts/forgot_password.html", context)

    return render(request, "accounts/forgot_password.html")


def reset_password(request, token):
    """Handle password reset with token."""
    try:
        profile = Profile.objects.get(password_reset_token=token)

        # Check token expiry (1 hour)
        if profile.password_reset_sent_at:
            expiry_time = profile.password_reset_sent_at + timedelta(hours=1)
            if timezone.now() > expiry_time:
                context = {"status": "expired"}
                return render(request, "accounts/reset_password.html", context)

        if request.method == "POST":
            password = request.POST.get("password")
            password_confirm = request.POST.get("password_confirm")

            errors = []

            # Validate passwords
            if not password:
                errors.append("Password is required.")
            elif len(password) < 8:
                errors.append("Password must be at least 8 characters long.")

            if password != password_confirm:
                errors.append("Passwords do not match.")

            if errors:
                context = {
                    "errors": errors,
                    "token": token,
                }
                return render(request, "accounts/reset_password.html", context)

            # Reset password
            user = profile.user
            user.set_password(password)
            user.save()

            # Clear reset token
            profile.password_reset_token = ""
            profile.password_reset_sent_at = None
            profile.save()

            context = {"status": "success"}
            return render(request, "accounts/reset_password.html", context)

        # Show form
        context = {"token": token}
        return render(request, "accounts/reset_password.html", context)

    except Profile.DoesNotExist:
        context = {"status": "invalid"}
        return render(request, "accounts/reset_password.html", context)


# =============================================================================
# API VIEWSETS (For DRF)
# =============================================================================


class WishlistViewSet(viewsets.ModelViewSet):
    """API viewset for wishlist management."""

    serializer_class = WishlistItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return WishlistItem.objects.filter(user=self.request.user)
        return WishlistItem.objects.none()
