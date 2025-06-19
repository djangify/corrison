# checkout/management/commands/recover_payment.py
from django.core.management.base import BaseCommand
from django.db import transaction
from checkout.models import Order, OrderItem, Payment
from accounts.models import User
from products.models import Product, ProductVariant
import stripe
from django.conf import settings
from decimal import Decimal

stripe.api_key = settings.STRIPE_SECRET_KEY


class Command(BaseCommand):
    help = "Recover a Stripe payment and create the missing order"

    def add_arguments(self, parser):
        parser.add_argument(
            "payment_intent_id", type=str, help="Stripe Payment Intent ID"
        )

    def handle(self, *args, **options):
        payment_intent_id = options["payment_intent_id"]

        try:
            # Get payment intent from Stripe
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            self.stdout.write(f"Found payment intent: {intent.id}")
            self.stdout.write(f"Amount: £{intent.amount / 100}")
            self.stdout.write(f"Status: {intent.status}")

            if intent.status != "succeeded":
                self.stdout.write(self.style.ERROR("Payment not succeeded"))
                return

            # Get metadata
            metadata = intent.metadata
            user_email = metadata.get("email")
            items_data = metadata.get("items", "[]")

            self.stdout.write(f"Email: {user_email}")
            self.stdout.write(f"Items data: {items_data}")

            # Find user
            user = User.objects.filter(email=user_email).first()
            if not user:
                self.stdout.write(self.style.ERROR(f"User not found: {user_email}"))
                return

            self.stdout.write(f"Found user: {user}")

            # Check if order already exists
            existing_order = Order.objects.filter(
                stripe_payment_intent_id=payment_intent_id
            ).first()
            if existing_order:
                self.stdout.write(
                    self.style.WARNING(
                        f"Order already exists: {existing_order.order_number}"
                    )
                )
                return

            # Parse items
            import json

            try:
                items = json.loads(items_data)
            except:
                self.stdout.write(self.style.ERROR("Could not parse items data"))
                return

            with transaction.atomic():
                # Create order
                order = Order.objects.create(
                    user=user,
                    stripe_payment_intent_id=payment_intent_id,
                    subtotal=Decimal(str(intent.amount / 100)),
                    shipping_cost=Decimal("0.00"),
                    tax_amount=Decimal("0.00"),
                    discount_amount=Decimal("0.00"),
                    total=Decimal(str(intent.amount / 100)),
                    payment_status="paid",
                    status="processing",
                    digital_delivery_email=user_email,
                )
                self.stdout.write(f"Created order: {order.order_number}")

                # Create order items
                for item_data in items:
                    variant_id = item_data.get("id")
                    quantity = item_data.get("quantity", 1)

                    # Get variant
                    variant = ProductVariant.objects.filter(id=variant_id).first()
                    if not variant:
                        self.stdout.write(
                            self.style.WARNING(f"Variant not found: {variant_id}")
                        )
                        continue

                    # Create order item
                    order_item = OrderItem.objects.create(
                        order=order,
                        product=variant.product,
                        variant=variant,
                        product_name=variant.product.title,
                        variant_name=variant.name,
                        sku=variant.sku,
                        price=variant.current_price,
                        quantity=quantity,
                        is_digital=variant.product.is_digital,
                    )

                    # Set up digital download if applicable
                    if order_item.is_digital:
                        order_item.setup_digital_product()

                    self.stdout.write(f"Created order item: {order_item.product_name}")

                # Create payment record
                payment = Payment.objects.create(
                    order=order,
                    payment_method="stripe",
                    transaction_id=payment_intent_id,
                    amount=order.total,
                    status="completed",
                    payment_data={"payment_intent": payment_intent_id},
                )
                self.stdout.write(f"Created payment record: {payment.id}")

                # Send confirmation email
                from checkout.services.checkout import CheckoutService

                CheckoutService.send_order_confirmation_email(order)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully recovered order: {order.order_number}"
                    )
                )

        except stripe.error.StripeError as e:
            self.stdout.write(self.style.ERROR(f"Stripe error: {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
