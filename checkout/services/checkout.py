# checkout/services/checkout.py - Updated for JWT tokens and no address collection
from decimal import Decimal
from django.conf import settings
from cart.models import Cart
from checkout.models import Order, OrderItem, Payment
import stripe

# Configure Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY


class CheckoutService:
    """
    Service class for handling the checkout process.
    """

    @staticmethod
    def create_order_from_cart(request, **kwargs):
        """
        Create a new order from the cart contents.
        No address collection - Stripe handles addresses.

        Args:
            request: The HTTP request
            **kwargs: Order data including 'cart_token', 'email', 'shipping_method', etc.

        Returns:
            tuple: (success, order, error_message)
        """
        # Get cart using token
        cart_token = kwargs.get("cart_token")
        cart = None

        if cart_token:
            from cart.utils import CartTokenManager

            cart_id = CartTokenManager.decode_cart_token(cart_token)
            if cart_id:
                cart = Cart.objects.filter(id=cart_id, is_active=True).first()

        # Fallback to user if authenticated and no cart found
        if not cart and request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user, is_active=True).first()

        if not cart:
            return False, None, "Cart not found."

        # Check if cart is empty
        if cart.items.count() == 0:
            return False, None, "Your cart is empty."

        # Calculate order totals
        subtotal = cart.subtotal

        # Determine if this is a digital-only order
        is_digital_only = cart.is_digital_only

        # Apply shipping cost (only for orders with physical items)
        shipping_cost = Decimal("0.00")
        shipping_method = kwargs.get("shipping_method")

        if not is_digital_only and shipping_method:
            if shipping_method == "standard":
                shipping_cost = Decimal("5.00")
            elif shipping_method == "express":
                shipping_cost = Decimal("15.00")

        # Apply tax (example: flat 10% - you may want to make this configurable)
        tax_rate = Decimal("0.10")
        tax_amount = subtotal * tax_rate

        # Apply discount if any (future feature)
        discount_amount = Decimal("0.00")

        # Calculate total
        total = subtotal + shipping_cost + tax_amount - discount_amount

        # Determine customer email
        customer_email = None
        if request.user.is_authenticated:
            customer_email = request.user.email
        else:
            customer_email = kwargs.get("email")

        if not customer_email:
            return False, None, "Customer email is required."

        # Create order
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            guest_email=customer_email if not request.user.is_authenticated else None,
            shipping_method=shipping_method if not is_digital_only else None,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total=total,
            customer_notes=kwargs.get("notes", ""),
            status="pending",
            payment_status="pending",
            payment_method=kwargs.get("payment_method", "stripe"),
            # Digital order fields
            has_digital_items=cart.has_digital_items,
            has_physical_items=cart.has_physical_items,
            digital_delivery_email=kwargs.get("digital_delivery_email")
            or customer_email,
        )

        # Create order items
        for cart_item in cart.items.select_related("product", "variant").all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                variant=cart_item.variant,
                product_name=cart_item.product.name,
                variant_name=str(cart_item.variant) if cart_item.variant else None,
                sku=cart_item.variant.sku
                if cart_item.variant
                else cart_item.product.sku,
                price=cart_item.unit_price,
                quantity=cart_item.quantity,
                # Digital product fields are set automatically in OrderItem.save()
            )

        # Clear the cart after order creation
        cart.clear()

        return True, order, None

    @staticmethod
    def create_payment_intent(order, payment_method="stripe"):
        """
        Create a payment intent for the order.

        Args:
            order: The order to create a payment intent for
            payment_method: The payment method to use

        Returns:
            tuple: (success, client_secret, error_message)
        """
        if payment_method == "stripe":
            try:
                # Determine if address collection is needed
                automatic_payment_methods = {
                    "enabled": True,
                }

                # Configure address collection
                shipping_config = None
                if order.has_physical_items:
                    shipping_config = {
                        "allowed_countries": [
                            "US",
                            "CA",
                            "GB",
                            "AU",
                        ],  # Add your countries
                    }

                # Create a payment intent with Stripe
                intent_data = {
                    "amount": int(order.total * 100),  # Convert to cents
                    "currency": "usd",
                    "automatic_payment_methods": automatic_payment_methods,
                    "metadata": {
                        "order_id": str(order.id),
                        "order_number": order.order_number,
                        "has_digital_items": str(order.has_digital_items),
                        "has_physical_items": str(order.has_physical_items),
                    },
                }

                # Add shipping if needed
                if shipping_config:
                    intent_data["shipping"] = shipping_config

                intent = stripe.PaymentIntent.create(**intent_data)

                return True, intent.client_secret, None
            except Exception as e:
                return False, None, str(e)
        else:
            return False, None, f"Payment method {payment_method} is not supported."

    @staticmethod
    def process_payment(
        order, transaction_id, payment_method="stripe", payment_data=None
    ):
        """
        Process a payment for an order.

        Args:
            order: The order to process payment for
            transaction_id: The transaction ID from the payment processor
            payment_method: The payment method used
            payment_data: Additional payment data

        Returns:
            tuple: (success, payment, error_message)
        """
        try:
            # Create a payment record
            payment = Payment.objects.create(
                order=order,
                payment_method=payment_method,
                transaction_id=transaction_id,
                amount=order.total,
                status="completed",
                payment_data=payment_data or {},
            )

            # Update the order status
            order.payment_status = "paid"
            order.status = "processing"
            order.save()

            return True, payment, None
        except Exception as e:
            return False, None, str(e)

    @staticmethod
    def handle_stripe_webhook(payload, sig_header):
        """
        Handle Stripe webhook events.

        Args:
            payload: The webhook payload
            sig_header: The Stripe signature header

        Returns:
            tuple: (success, order, error_message)
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )

            # Handle the event
            if event.type == "payment_intent.succeeded":
                payment_intent = event.data.object

                # Find the order by the payment intent metadata
                order_id = payment_intent.metadata.get("order_id")
                if not order_id:
                    return False, None, "Order ID not found in payment intent metadata."

                try:
                    order = Order.objects.get(id=order_id)
                except Order.DoesNotExist:
                    return False, None, f"Order with ID {order_id} not found."

                # Process the payment
                success, payment, error = CheckoutService.process_payment(
                    order=order,
                    transaction_id=payment_intent.id,
                    payment_method="stripe",
                    payment_data=payment_intent,
                )

                if not success:
                    return False, order, error

                return True, order, None

            elif event.type == "payment_intent.payment_failed":
                payment_intent = event.data.object

                # Find the order by the payment intent metadata
                order_id = payment_intent.metadata.get("order_id")
                if not order_id:
                    return False, None, "Order ID not found in payment intent metadata."

                try:
                    order = Order.objects.get(id=order_id)
                except Order.DoesNotExist:
                    return False, None, f"Order with ID {order_id} not found."

                # Update the order status
                order.payment_status = "failed"
                order.save()

                return True, order, None

            return True, None, None

        except ValueError as e:
            return False, None, f"Invalid payload: {str(e)}"
        except stripe.error.SignatureVerificationError as e:
            return False, None, f"Invalid signature: {str(e)}"
        except Exception as e:
            return False, None, f"Error processing webhook: {str(e)}"


class OrderService:
    """
    Service class for handling order-related operations.
    """

    @staticmethod
    def get_user_orders(user, **filters):
        """
        Get orders for a specific user.

        Args:
            user: The user to get orders for
            **filters: Additional filters

        Returns:
            QuerySet: A queryset of orders
        """
        orders = Order.objects.filter(user=user)

        # Apply filters
        status = filters.get("status")
        if status:
            orders = orders.filter(status=status)

        # Apply date filters
        date_from = filters.get("date_from")
        date_to = filters.get("date_to")

        if date_from:
            orders = orders.filter(created_at__gte=date_from)

        if date_to:
            orders = orders.filter(created_at__lte=date_to)

        return orders.order_by("-created_at")

    @staticmethod
    def get_order_by_number(order_number, user=None):
        """
        Get an order by its number, optionally filtering by user.

        Args:
            order_number: The order number
            user: The user to filter by (optional)

        Returns:
            Order: The order or None if not found
        """
        try:
            if user:
                return Order.objects.get(order_number=order_number, user=user)
            return Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            return None

    @staticmethod
    def cancel_order(order):
        """
        Cancel an order if possible.

        Args:
            order: The order to cancel

        Returns:
            tuple: (success, message)
        """
        if not order.can_cancel:
            return False, "This order cannot be cancelled."

        order.status = "cancelled"
        order.save()

        return True, "Order cancelled successfully."
