from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from core.models import TimestampedModel
from products.models import Product, ProductVariant

User = get_user_model()


class Order(TimestampedModel):
    """
    Order model to store order information.
    """

    ORDER_STATUS_CHOICES = (
        ("pending", _("Pending")),
        ("processing", _("Processing")),
        ("shipped", _("Shipped")),
        ("delivered", _("Delivered")),
        ("cancelled", _("Cancelled")),
        ("refunded", _("Refunded")),
    )

    PAYMENT_STATUS_CHOICES = (
        ("pending", _("Pending")),
        ("paid", _("Paid")),
        ("failed", _("Failed")),
        ("refunded", _("Refunded")),
    )

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name="orders", null=True, blank=True
    )
    guest_email = models.EmailField(blank=True, null=True)
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(
        max_length=20, choices=ORDER_STATUS_CHOICES, default="pending"
    )
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending"
    )

    # Digital order support
    has_digital_items = models.BooleanField(default=False)
    has_physical_items = models.BooleanField(default=False)
    digital_delivery_email = models.EmailField(
        blank=True,
        null=True,
        help_text="Email for digital product delivery (if different from customer email)",
    )

    # Appointment support - add these fields after admin_notes
    appointment_type = models.ForeignKey(
        "appointments.AppointmentType",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="orders",
        help_text="If this order is for an appointment booking",
    )
    appointment_date = models.DateField(null=True, blank=True)
    appointment_start_time = models.TimeField(null=True, blank=True)
    appointment_customer_name = models.CharField(max_length=200, blank=True)
    appointment_customer_phone = models.CharField(max_length=20, blank=True)
    appointment_notes = models.TextField(blank=True)

    # Tracking info (only for physical items)
    shipping_method = models.CharField(max_length=100, blank=True, null=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)

    # Totals
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # Payment information
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    payment_id = models.CharField(max_length=255, blank=True, null=True)

    # Notes
    customer_notes = models.TextField(blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order_number"]),
            models.Index(fields=["user"]),
            models.Index(fields=["status"]),
            models.Index(fields=["payment_status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["has_digital_items"]),
            models.Index(fields=["has_physical_items"]),
        ]

    def __str__(self):
        return f"Order {self.order_number}"

    def get_customer_email(self):
        """
        Return the customer email, either from the user or the guest_email field.
        """
        if self.user:
            return self.user.email
        return self.guest_email

    def get_delivery_email(self):
        """
        Return the delivery email for digital products.
        """
        return self.digital_delivery_email or self.get_customer_email()

    @property
    def is_paid(self):
        """
        Check if the order is paid.
        """
        return self.payment_status == "paid"

    @property
    def can_cancel(self):
        """
        Check if the order can be cancelled.
        """
        return self.status in ["pending", "processing"]

    @property
    def is_completed(self):
        """
        Check if the order is completed.
        """
        return self.status in ["delivered"]

    @property
    def is_digital_only(self):
        """
        Returns True if order contains only digital items.
        """
        return self.has_digital_items and not self.has_physical_items

    @property
    def is_appointment_order(self):
        """Check if this order is for an appointment"""
        return self.appointment_type is not None

    @property
    def requires_shipping(self):
        """
        Returns True if order contains physical items that need shipping.
        """
        return self.has_physical_items

    def generate_order_number(self):
        """
        Generate a unique order number.
        """
        import random
        import string

        order_number = "".join(random.choices(string.digits, k=8))

        # Check if order number exists
        if Order.objects.filter(order_number=order_number).exists():
            return self.generate_order_number()

        return order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()

        if not self.total:
            self.total = self.calculate_total()

        super().save(*args, **kwargs)

    def calculate_total(self):
        """
        Calculate order total.
        """
        return (
            self.subtotal + self.shipping_cost + self.tax_amount - self.discount_amount
        )


class OrderItem(TimestampedModel):
    """
    Order item model to store items in an order.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.PROTECT, blank=True, null=True
    )
    product_name = models.CharField(max_length=255)
    variant_name = models.CharField(max_length=255, blank=True, null=True)
    sku = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    # Digital product fields
    is_digital = models.BooleanField(default=False)
    download_token = models.CharField(max_length=255, blank=True, unique=True)
    download_expires_at = models.DateTimeField(null=True, blank=True)
    download_count = models.PositiveIntegerField(default=0)
    max_downloads = models.PositiveIntegerField(default=5)

    class Meta:
        verbose_name = _("Order Item")
        verbose_name_plural = _("Order Items")
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["product"]),
            models.Index(fields=["sku"]),
            models.Index(fields=["download_token"]),
            models.Index(fields=["is_digital"]),
        ]

    def __str__(self):
        if self.variant_name:
            return f"{self.quantity} x {self.product_name} ({self.variant_name})"
        return f"{self.quantity} x {self.product_name}"

    @property
    def total_price(self):
        """
        Calculate the total price for this item.
        """
        return self.price * self.quantity

    @property
    def can_download(self):
        """
        Check if this digital item can still be downloaded.
        """
        if not self.is_digital or not self.download_token:
            return False

        # Check expiry
        if self.download_expires_at:
            from django.utils import timezone

            if timezone.now() > self.download_expires_at:
                return False

        # Check download limit
        if self.max_downloads > 0 and self.download_count >= self.max_downloads:
            return False

        return True

    def get_download_file(self):
        """
        Get the file to download for this order item.
        """
        if self.variant and hasattr(self.variant, "effective_digital_file"):
            return self.variant.effective_digital_file
        return self.product.digital_file

    def generate_download_token(self):
        """
        Generate a unique download token for this item.
        """
        import secrets

        token = secrets.token_urlsafe(32)

        # Ensure uniqueness
        while OrderItem.objects.filter(download_token=token).exists():
            token = secrets.token_urlsafe(32)

        return token

    def save(self, *args, **kwargs):
        """
        Override save to handle digital product setup.
        """
        # Set is_digital based on product type
        self.is_digital = self.product.is_digital

        # Generate download token for digital products
        if self.is_digital and not self.download_token:
            self.download_token = self.generate_download_token()

            # Set download expiry
            if self.product.download_expiry_days:
                from django.utils import timezone
                from datetime import timedelta

                self.download_expires_at = timezone.now() + timedelta(
                    days=self.product.download_expiry_days
                )

            # Set download limit
            if self.product.download_limit:
                self.max_downloads = self.product.download_limit

        super().save(*args, **kwargs)


class Payment(TimestampedModel):
    """
    Payment model to store payment information.
    """

    PAYMENT_METHOD_CHOICES = (
        ("stripe", _("Stripe")),
        ("paypal", _("PayPal")),
        ("bank_transfer", _("Bank Transfer")),
    )

    PAYMENT_STATUS_CHOICES = (
        ("pending", _("Pending")),
        ("completed", _("Completed")),
        ("failed", _("Failed")),
        ("refunded", _("Refunded")),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending"
    )
    payment_data = models.JSONField(blank=True, null=True)

    class Meta:
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["transaction_id"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Payment {self.transaction_id} for Order {self.order.order_number}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Update order payment status if needed
        if self.status == "completed" and self.order.payment_status != "paid":
            self.order.payment_status = "paid"
            self.order.save()
        elif self.status == "refunded" and self.order.payment_status != "refunded":
            self.order.payment_status = "refunded"
            self.order.save()
