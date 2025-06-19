# checkout/services/checkout.py
from django.db import transaction
from decimal import Decimal
from cart.models import Cart
from checkout.models import Order, OrderItem
import logging

logger = logging.getLogger(__name__)


class CheckoutService:
    """Service for handling checkout operations"""

    @staticmethod
    @transaction.atomic
    def create_order_from_cart(request, **kwargs):
        """
        Create an order from the current cart
        """
        try:
            # Get cart - use session for anonymous or user for authenticated
            user = request.user if request.user.is_authenticated else None
            cart = None

            if user:
                # For authenticated users, get their cart
                cart = Cart.objects.filter(user=user, is_active=True).first()
            else:
                # For anonymous users, use session
                session_key = request.session.session_key
                if session_key:
                    cart = Cart.objects.filter(
                        session_key=session_key, user__isnull=True, is_active=True
                    ).first()

            if not cart or not cart.items.exists():
                return False, None, "Cart is empty"

            # Create order
            order = Order.objects.create(
                user=user,
                guest_email=kwargs.get("email", ""),
                digital_delivery_email=kwargs.get(
                    "digital_delivery_email", kwargs.get("email", "")
                ),
                subtotal=cart.subtotal,
                shipping_cost=Decimal("0.00"),  # Digital only - no shipping
                tax_amount=Decimal("0.00"),  # Simplified - no tax calculation
                discount_amount=Decimal("0.00"),
                total=cart.subtotal,
                customer_notes=kwargs.get("notes", ""),
                payment_status="unpaid",
                status="pending",
                has_digital_items=cart.has_digital_items,
                has_physical_items=cart.has_physical_items,
            )

            # Store payment intent ID if provided
            if "stripe_payment_intent_id" in kwargs:
                order.stripe_payment_intent_id = kwargs["stripe_payment_intent_id"]
                order.save()

            # Create order items
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    variant=cart_item.variant,
                    product_name=cart_item.product.name,
                    variant_name=cart_item.variant.name if cart_item.variant else "",
                    sku=cart_item.product.sku
                    if hasattr(cart_item.product, "sku")
                    else "",
                    price=cart_item.unit_price,
                    quantity=cart_item.quantity,
                    is_digital=cart_item.product.is_digital,
                )

                # Note: Digital product setup happens when payment is marked as complete
                # via Payment.save() method which calls setup_digital_product()

            # Update order totals to include digital/physical item flags
            order.has_digital_items = any(item.is_digital for item in order.items.all())
            order.has_physical_items = any(
                not item.is_digital for item in order.items.all()
            )
            order.save()

            # Clear the cart
            cart.clear()

            # Log order creation
            logger.info(f"Order {order.order_number} created successfully")

            return True, order, None

        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            return False, None, str(e)

    @staticmethod
    def send_order_confirmation_email(order):
        """
        Send order confirmation email with download links
        """
        from accounts.utils import send_order_confirmation_email as send_email

        try:
            send_email(order)
            logger.info(f"Order confirmation email sent for order {order.order_number}")
        except Exception as e:
            logger.error(f"Failed to send order confirmation email: {str(e)}")

    @staticmethod
    def process_successful_payment(order):
        """
        Process successful payment - enable downloads and send emails
        """
        try:
            # Update order status
            order.payment_status = "paid"
            order.status = "processing"
            order.save()

            # Set up digital downloads for all digital items
            for item in order.items.filter(is_digital=True):
                item.setup_digital_product()

            # Send order confirmation email
            CheckoutService.send_order_confirmation_email(order)

            # If order is digital only, mark as completed
            if order.is_digital_only:
                order.mark_as_completed()

            logger.info(
                f"Successfully processed payment for order {order.order_number}"
            )

        except Exception as e:
            logger.error(f"Error processing successful payment: {str(e)}")
