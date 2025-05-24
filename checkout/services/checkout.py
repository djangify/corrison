# checkout/services/checkout.py - Updated create_order_from_cart method
from decimal import Decimal
from django.conf import settings
from cart.models import Cart
from checkout.models import Order, OrderItem, Address, Payment
import stripe

# Configure Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY


class CheckoutService:
    """
    Service class for handling the checkout process.
    """
    
    @staticmethod
    def create_order_from_cart(request, billing_address, shipping_address=None, **kwargs):
        """
        Create a new order from the cart contents.
        
        Args:
            request: The HTTP request
            billing_address: Billing address data or Address instance
            shipping_address: Shipping address data or Address instance (optional)
            **kwargs: Additional order data including 'cart_token'
            
        Returns:
            tuple: (success, order, error_message)
        """
        # Get cart using token or user
        cart_token = kwargs.get('cart_token')
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
        
        # Get or create the address objects
        billing_address_obj = CheckoutService._get_or_create_address(
            request, billing_address, is_default_billing=True
        )
        
        if shipping_address:
            shipping_address_obj = CheckoutService._get_or_create_address(
                request, shipping_address, is_default_shipping=True
            )
        else:
            # Use billing address as shipping address
            shipping_address_obj = billing_address_obj
        
        # Calculate order totals
        subtotal = cart.subtotal
        
        # Apply shipping cost
        shipping_cost = Decimal('0.00')
        shipping_method = kwargs.get('shipping_method')
        if shipping_method == 'standard':
            shipping_cost = Decimal('5.00')
        elif shipping_method == 'express':
            shipping_cost = Decimal('15.00')
        
        # Apply tax (example: flat 10%)
        tax_rate = Decimal('0.10')
        tax_amount = subtotal * tax_rate
        
        # Apply discount if any
        discount_amount = Decimal('0.00')
        
        # Calculate total
        total = subtotal + shipping_cost + tax_amount - discount_amount
        
        # Create order
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            guest_email=kwargs.get('email') if not request.user.is_authenticated else None,
            billing_address=billing_address_obj,
            shipping_address=shipping_address_obj,
            shipping_method=shipping_method,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total=total,
            customer_notes=kwargs.get('notes', ''),
            status='pending',
            payment_status='pending',
        )
        
        # Create order items
        for cart_item in cart.items.select_related('product', 'variant').all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                variant=cart_item.variant,
                product_name=cart_item.product.name,
                variant_name=str(cart_item.variant) if cart_item.variant else None,
                sku=cart_item.variant.sku if cart_item.variant else cart_item.product.sku,
                price=cart_item.unit_price,
                quantity=cart_item.quantity,
            )
        
        # Clear the cart after order creation
        cart.clear()
        
        return True, order, None
    
    @staticmethod
    def _get_or_create_address(request, address_data, is_default_shipping=False, is_default_billing=False):
        """
        Get or create an address object.
        
        Args:
            request: The HTTP request
            address_data: Address data or Address instance
            is_default_shipping: Whether this is the default shipping address
            is_default_billing: Whether this is the default billing address
            
        Returns:
            Address: The address object
        """
        # If address_data is already an Address instance, return it
        if isinstance(address_data, Address):
            return address_data
        
        # If user is authenticated, create an address associated with the user
        if request.user.is_authenticated:
            return Address.objects.create(
                user=request.user,
                full_name=address_data.get('full_name'),
                address_line1=address_data.get('address_line1'),
                address_line2=address_data.get('address_line2', ''),
                city=address_data.get('city'),
                state_province=address_data.get('state_province'),
                postal_code=address_data.get('postal_code'),
                country=address_data.get('country'),
                phone=address_data.get('phone'),
                is_default_shipping=is_default_shipping,
                is_default_billing=is_default_billing,
            )
        
        # For guest users, create an address without a user association
        return Address.objects.create(
            full_name=address_data.get('full_name'),
            address_line1=address_data.get('address_line1'),
            address_line2=address_data.get('address_line2', ''),
            city=address_data.get('city'),
            state_province=address_data.get('state_province'),
            postal_code=address_data.get('postal_code'),
            country=address_data.get('country'),
            phone=address_data.get('phone'),
            is_default_shipping=is_default_shipping,
            is_default_billing=is_default_billing,
        )
    
    # Keep all other existing methods unchanged...
    @staticmethod
    def create_payment_intent(order, payment_method='stripe'):
        """
        Create a payment intent for the order.
        
        Args:
            order: The order to create a payment intent for
            payment_method: The payment method to use
            
        Returns:
            tuple: (success, client_secret, error_message)
        """
        if payment_method == 'stripe':
            try:
                # Create a payment intent with Stripe
                intent = stripe.PaymentIntent.create(
                    amount=int(order.total * 100),  # Convert to cents
                    currency='usd',
                    metadata={
                        'order_id': str(order.id),
                        'order_number': order.order_number,
                    },
                )
                
                return True, intent.client_secret, None
            except Exception as e:
                return False, None, str(e)
        else:
            return False, None, f"Payment method {payment_method} is not supported."
    
    @staticmethod
    def process_payment(order, transaction_id, payment_method='stripe', payment_data=None):
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
                status='completed',
                payment_data=payment_data or {},
            )
            
            # Update the order status
            order.payment_status = 'paid'
            order.status = 'processing'
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
            if event.type == 'payment_intent.succeeded':
                payment_intent = event.data.object
                
                # Find the order by the payment intent metadata
                order_id = payment_intent.metadata.get('order_id')
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
                    payment_method='stripe',
                    payment_data=payment_intent,
                )
                
                if not success:
                    return False, order, error
                
                return True, order, None
                
            elif event.type == 'payment_intent.payment_failed':
                payment_intent = event.data.object
                
                # Find the order by the payment intent metadata
                order_id = payment_intent.metadata.get('order_id')
                if not order_id:
                    return False, None, "Order ID not found in payment intent metadata."
                
                try:
                    order = Order.objects.get(id=order_id)
                except Order.DoesNotExist:
                    return False, None, f"Order with ID {order_id} not found."
                
                # Update the order status
                order.payment_status = 'failed'
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
        status = filters.get('status')
        if status:
            orders = orders.filter(status=status)
        
        # Apply date filters
        date_from = filters.get('date_from')
        date_to = filters.get('date_to')
        
        if date_from:
            orders = orders.filter(created_at__gte=date_from)
        
        if date_to:
            orders = orders.filter(created_at__lte=date_to)
        
        return orders.order_by('-created_at')
    
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
        
        order.status = 'cancelled'
        order.save()
        
        return True, "Order cancelled successfully."