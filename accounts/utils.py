# accounts/utils.py
import uuid
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


def generate_verification_token():
    """Generate a unique verification token"""
    return str(uuid.uuid4())


def send_verification_email(user, token):
    """Send email verification email to user"""

    # Create verification URL
    verification_url = f"{getattr(settings, 'EMAIL_VERIFICATION_URL', 'https://corrisonapi.com/auth/verify-email')}/{token}/"

    subject = f"Please verify your email address - {getattr(settings, 'SITE_NAME', 'Corrison')}"

    # Text message (fallback)
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
        # Try to use HTML template, fallback to text if template doesn't exist
        try:
            html_message = render_to_string(
                "emails/verification_email.html",
                {
                    "user": user,
                    "verification_url": verification_url,
                    "site_name": getattr(settings, "SITE_NAME", "Corrison"),
                    "token": token,
                },
            )
        except Exception:
            html_message = None

        send_mail(
            subject=subject,
            message=message,  # Keep text fallback
            html_message=html_message,  # Add HTML version if available
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "hello@corrisonapi.com"),
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

    # Text message
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
        # Try to use HTML template, fallback to text if template doesn't exist
        try:
            html_message = render_to_string(
                "emails/welcome_email.html",
                {
                    "user": user,
                    "site_name": getattr(settings, "SITE_NAME", "Corrison"),
                },
            )
        except Exception:
            html_message = None

        send_mail(
            subject=subject,
            message=message,
            html_message=html_message,  # Add HTML version if available
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "hello@corrisonapi.com"),
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send welcome email: {e}")
        return False


def send_password_reset_email(user, reset_token):
    """Send password reset email"""

    # Create reset URL
    reset_url = f"{getattr(settings, 'PASSWORD_RESET_URL', 'https://corrisonapi.com/auth/reset-password')}/{reset_token}/"

    subject = f"Reset your password - {getattr(settings, 'SITE_NAME', 'Corrison')}"

    # Text message
    message = f"""
Hello {user.get_full_name() or user.username},

You requested a password reset for your {getattr(settings, "SITE_NAME", "Corrison")} account.

To reset your password, click the link below:

{reset_url}

This reset link will expire in 1 hour for security reasons.

If you didn't request this reset, please ignore this email.

Best regards,
The {getattr(settings, "SITE_NAME", "Corrison")} Team
"""

    try:
        # Try to use HTML template, fallback to text if template doesn't exist
        try:
            html_message = render_to_string(
                "emails/password_reset_email.html",
                {
                    "user": user,
                    "reset_url": reset_url,
                    "site_name": getattr(settings, "SITE_NAME", "Corrison"),
                },
            )
        except Exception:
            html_message = None

        send_mail(
            subject=subject,
            message=message,
            html_message=html_message,  # Add HTML version if available
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "hello@corrisonapi.com"),
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send password reset email: {e}")
        return False
