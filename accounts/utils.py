# accounts/utils.py
import uuid
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse


def generate_verification_token():
    """Generate a unique verification token"""
    return str(uuid.uuid4())


def send_verification_email(user, token):
    """Send email verification email to user"""

    # Create verification URL
    verification_url = f"{getattr(settings, 'EMAIL_VERIFICATION_URL', 'http://localhost:8000/api/v1/auth/verify-email')}/{token}/"

    subject = f"Please verify your email address - {getattr(settings, 'SITE_NAME', 'Corrison')}"

    # Email context
    context = {
        "user": user,
        "verification_url": verification_url,
        "site_name": getattr(settings, "SITE_NAME", "Corrison"),
        "token": token,
    }

    # For now, we'll send a simple text email
    # You can create HTML templates later
    message = f"""
Hello {user.get_full_name() or user.username},

Thank you for registering with {getattr(settings, "SITE_NAME", "Corrison")}!

To complete your registration, please verify your email address by clicking the link below:

{verification_url}

This verification link will expire in {getattr(settings, "EMAIL_VERIFICATION_TOKEN_EXPIRY", 24)} hours.

If you didn't create an account with us, please ignore this email.

Best regards,
The {getattr(settings, "SITE_NAME", "Corrison")} Team
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(
                settings, "DEFAULT_FROM_EMAIL", "noreply@corrisonapi.com"
            ),
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send verification email: {e}")
        return False


def send_welcome_email(user):
    """Send welcome email after successful verification"""

    subject = f"Welcome to {getattr(settings, 'SITE_NAME', 'Corrison')} - Your account is ready!"

    message = f"""
Hello {user.get_full_name() or user.username},

Welcome to {getattr(settings, "SITE_NAME", "Corrison")}! 

Your email address has been successfully verified and your account is now active.

You can now:
- Browse our products and add items to your wishlist
- Enroll in courses and track your progress
- Make purchases with your verified account
- Access all member features

Thank you for joining our community!

Best regards,
The {getattr(settings, "SITE_NAME", "Corrison")} Team
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(
                settings, "DEFAULT_FROM_EMAIL", "noreply@corrisonapi.com"
            ),
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send welcome email: {e}")
        return False


def send_password_reset_email(user, reset_token):
    """Send password reset email (for future implementation)"""

    subject = f"Reset your password - {getattr(settings, 'SITE_NAME', 'Corrison')}"

    # This would be implemented when you add password reset functionality
    message = f"""
Hello {user.get_full_name() or user.username},

You requested a password reset for your {getattr(settings, "SITE_NAME", "Corrison")} account.

[Password reset functionality to be implemented]

If you didn't request this reset, please ignore this email.

Best regards,
The {getattr(settings, "SITE_NAME", "Corrison")} Team
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(
                settings, "DEFAULT_FROM_EMAIL", "noreply@corrisonapi.com"
            ),
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send password reset email: {e}")
        return False
