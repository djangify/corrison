from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from core.models import TimestampedModel, UUIDModel
from products.models import Product, ProductVariant

User = get_user_model()

class Address(UUIDModel, TimestampedModel):
    """
    Address model for shipping and billing addresses.
    """
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, 
        related_name='addresses'
    )
    full_name = models.CharField(max_length=255)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    phone = models.CharField(max_length=50)
    is_default_shipping = models.BooleanField(default=False)
    is_default_billing = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _('Address')
        verbose_name_plural = _('Addresses')
        ordering = ['-is_default_shipping', '-is_default_billing', '-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_default_shipping']),
            models.Index(fields=['is_default_billing']),
        ]
    
    def __str__(self):
        return f"{self.full_name}, {self.address_line1}, {self.city}"
    
    def save(self, *args, **kwargs):
        # If this is set as default, unset any other defaults
        if self.is_default_shipping:
            Address.objects.filter(
                user=self.user, 
                is_default_shipping=True
            ).update(is_default_shipping=False)
            
        if self.is_default_billing:
            Address.objects.filter(
                user=self.user, 
                is_default_billing=True
            ).update(is_default_billing=False)
            
        super().save(*args, **kwargs)


class Order(UUIDModel, TimestampedModel):
    """
    Order model to store order information.
    """
    ORDER_STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('shipped', _('Shipped')),
        ('delivered', _('Delivered')),
        ('cancelled', _('Cancelled')),
        ('refunded', _('Refunded')),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('paid', _('Paid')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
    )
    
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, 
        related_name='orders',
        null=True, blank=True
    )
    guest_email = models.EmailField(blank=True, null=True)
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(
        max_length=20, 
        choices=ORDER_STATUS_CHOICES,
        default='pending'
    )
    payment_status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    
    # Addresses
    shipping_address = models.ForeignKey(
        Address, on_delete=models.PROTECT,
        related_name='shipping_orders',
        blank=True, null=True
    )
    billing_address = models.ForeignKey(
        Address, on_delete=models.PROTECT,
        related_name='billing_orders',
        blank=True, null=True
    )
    
    # Tracking info
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
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['created_at']),
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
    
    @property
    def is_paid(self):
        """
        Check if the order is paid.
        """
        return self.payment_status == 'paid'
    
    @property
    def can_cancel(self):
        """
        Check if the order can be cancelled.
        """
        return self.status in ['pending', 'processing']
    
    @property
    def is_completed(self):
        """
        Check if the order is completed.
        """
        return self.status in ['delivered']
    
    def generate_order_number(self):
        """
        Generate a unique order number.
        """
        import random
        import string
        
        order_number = ''.join(random.choices(string.digits, k=8))
        
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
        return self.subtotal + self.shipping_cost + self.tax_amount - self.discount_amount


class OrderItem(UUIDModel, TimestampedModel):
    """
    Order item model to store items in an order.
    """
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, 
        related_name='items'
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT
    )
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.PROTECT,
        blank=True, null=True
    )
    product_name = models.CharField(max_length=255)
    variant_name = models.CharField(max_length=255, blank=True, null=True)
    sku = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    
    class Meta:
        verbose_name = _('Order Item')
        verbose_name_plural = _('Order Items')
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['product']),
            models.Index(fields=['sku']),
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
        

class Payment(UUIDModel, TimestampedModel):
    """
    Payment model to store payment information.
    """
    PAYMENT_METHOD_CHOICES = (
        ('stripe', _('Stripe')),
        ('paypal', _('PayPal')),
        ('bank_transfer', _('Bank Transfer')),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
    )
    
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, 
        related_name='payments'
    )
    payment_method = models.CharField(
        max_length=50, 
        choices=PAYMENT_METHOD_CHOICES
    )
    transaction_id = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    payment_data = models.JSONField(blank=True, null=True)
    
    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Payment {self.transaction_id} for Order {self.order.order_number}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update order payment status if needed
        if self.status == 'completed' and self.order.payment_status != 'paid':
            self.order.payment_status = 'paid'
            self.order.save()
        elif self.status == 'refunded' and self.order.payment_status != 'refunded':
            self.order.payment_status = 'refunded'
            self.order.save()
            