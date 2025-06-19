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
    verification_url = f"{getattr(settings, 'EMAIL_VERIFICATION_URL', 'https://corrison.corrisonapi.com/auth/verify-email')}/{token}/"

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
    reset_url = f"{getattr(settings, 'PASSWORD_RESET_URL', 'https://corrison.corrisonapi.com/auth/reset-password')}/{reset_token}/"

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


def send_order_confirmation_email(order, user=None, guest_email=None):
    """Send order confirmation email - NO DIRECT DOWNLOAD LINKS for security"""

    # Determine recipient email
    recipient_email = None
    recipient_name = "Customer"

    if user and user.email:
        recipient_email = user.email
        recipient_name = user.get_full_name() or user.username
    elif guest_email:
        recipient_email = guest_email
    elif order.guest_email:
        recipient_email = order.guest_email

    if not recipient_email:
        print("No recipient email found for order confirmation")
        return False

    subject = f"Order Confirmation #{order.order_number} - {getattr(settings, 'SITE_NAME', 'Corrison')}"

    # Get order items with digital products
    digital_items = []
    physical_items = []

    for item in order.items.all():
        if item.is_digital:
            digital_items.append(item)
        else:
            physical_items.append(item)

    # Create order confirmation URL
    order_url = f"{getattr(settings, 'SITE_URL', 'https://corrisonapi.com')}/order-confirmation/{order.order_number}/"

    # Text message (fallback)
    message = f"""
Hello {recipient_name},

Thank you for your order from {getattr(settings, "SITE_NAME", "Corrison")}!

Order Number: {order.order_number}
Order Date: {order.created_at.strftime("%B %d, %Y")}
Total: ${order.total}

ORDER DETAILS:
"""

    # Add items to text message
    for item in order.items.all():
        message += (
            f"\n- {item.product_name} (Qty: {item.quantity}) - ${item.total_price}"
        )
        if item.is_digital:
            message += " [Digital Download]"

    message += f"\n\nSubtotal: ${order.subtotal}"
    if order.tax_amount:
        message += f"\nTax: ${order.tax_amount}"
    message += f"\nTotal: ${order.total}"

    # Add download instructions for digital items - NO DIRECT LINKS
    if digital_items:
        message += "\n\nDIGITAL DOWNLOADS:"
        message += "\nYour digital products are ready for download!"

        if user and user.profile.email_verified:
            message += "\n\nTo access your downloads:"
            message += f"\n1. Log in to your account at {getattr(settings, 'SITE_URL', 'https://corrisonapi.com')}/login"
            message += "\n2. Go to 'My Products' or 'Downloads' in your dashboard"
            message += "\n3. Click the download button next to each product"
        else:
            message += "\n\nIMPORTANT: To access your downloads:"
            message += (
                "\n1. Verify your email address (check for our verification email)"
            )
            message += f"\n2. Log in to your account at {getattr(settings, 'SITE_URL', 'https://corrisonapi.com')}/login"
            message += "\n3. Go to 'My Products' or 'Downloads' in your dashboard"
            message += "\n4. Click the download button next to each product"

        message += "\n\nYour downloads are secure and can only be accessed when logged into your account."

    message += f"\n\nYou can view your complete order details here:\n{order_url}"

    message += f"""

Need help? Contact our support team at {getattr(settings, "SUPPORT_EMAIL", "support@corrison.com")}

Thank you for your purchase!

Best regards,
The {getattr(settings, "SITE_NAME", "Corrison")} Team
"""

    try:
        # Try to use HTML template
        try:
            html_message = render_to_string(
                "emails/order_confirmation.html",
                {
                    "order": order,
                    "user": user,
                    "recipient_name": recipient_name,
                    "site_name": getattr(settings, "SITE_NAME", "Corrison"),
                    "site_url": getattr(
                        settings, "SITE_URL", "https://corrisonapi.com"
                    ),
                    "login_url": f"{getattr(settings, 'SITE_URL', 'https://corrisonapi.com')}/login",
                    "order_url": order_url,
                    "digital_items": digital_items,
                    "physical_items": physical_items,
                    "has_digital_items": len(digital_items) > 0,
                    "email_verified": user.profile.email_verified if user else False,
                    "support_email": getattr(
                        settings, "SUPPORT_EMAIL", "support@corrison.com"
                    ),
                },
            )
        except Exception:
            html_message = None

        send_mail(
            subject=subject,
            message=message,
            html_message=html_message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "hello@corrisonapi.com"),
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send order confirmation email: {e}")
        return False


def send_download_ready_email(order_item, user):
    """Send email when downloads are ready - directs to login, NO DIRECT LINKS"""

    if not user or not user.email:
        return False

    subject = f"Your downloads are ready - {order_item.product_name}"

    login_url = f"{getattr(settings, 'SITE_URL', 'https://corrisonapi.com')}/login"

    message = f"""
Hello {user.get_full_name() or user.username},

Great news! Your digital downloads are now available in your account.

Product: {order_item.product_name}
Order #: {order_item.order.order_number}

TO ACCESS YOUR DOWNLOADS:
1. Log in to your account: {login_url}
2. Go to "My Products" or "Downloads" from your dashboard
3. Find "{order_item.product_name}" and click the Download button

Download Details:
- Downloads remaining: {order_item.max_downloads if order_item.max_downloads else "Unlimited"}
- Expires: {order_item.download_expires_at.strftime("%B %d, %Y") if order_item.download_expires_at else "Never"}

Your downloads are secure and require you to be logged into your account.

Need help? Contact support at {getattr(settings, "SUPPORT_EMAIL", "support@corrison.com")}

Best regards,
The {getattr(settings, "SITE_NAME", "Corrison")} Team
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "hello@corrisonapi.com"),
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send download ready email: {e}")
        return False
