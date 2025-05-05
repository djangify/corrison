from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from core.models import TimestampedModel, SluggedModel, PublishableModel, SEOModel, UUIDModel
from tinymce.models import HTMLField
from django.conf import settings


class Category(SluggedModel, TimestampedModel, PublishableModel, SEOModel):
    """
    Product category model.
    """
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True, 
        related_name='children', on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to='categories', blank=True, null=True)
    
    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('products:category_detail', args=[self.slug])


class ProductManager(models.Manager):
    """
    Custom manager for Product model.
    """
    def active(self):
        """
        Returns all active products.
        """
        return self.filter(is_active=True)
    
    def featured(self):
        """
        Returns all featured products.
        """
        return self.active().filter(is_featured=True)
    
    def get_by_category(self, category_slug):
        """
        Returns all products in the given category.
        """
        return self.active().filter(category__slug=category_slug)


class Product(SluggedModel, TimestampedModel, PublishableModel, SEOModel):
    """
    Product model.
    """
    category = models.ForeignKey(
        Category, related_name='products', 
        on_delete=models.CASCADE
    )
    sku = models.CharField(max_length=100, unique=True)
    description = HTMLField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(
        max_digits=10, decimal_places=2, 
        blank=True, null=True
    )
    is_featured = models.BooleanField(default=False)
    in_stock = models.BooleanField(default=True)
    stock_qty = models.PositiveIntegerField(default=0)
    
    # Image fields
    main_image = models.ImageField(upload_to='products')
    
    # SEO fields (inherited from SEOModel)
    
    objects = ProductManager()
    
    class Meta:
        verbose_name = _('Product')
        verbose_name_plural = _('Products')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['in_stock']),
            models.Index(fields=['sku']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('products:product_detail', args=[self.slug])
    
    @property
    def is_on_sale(self):
        """
        Returns True if product has a sale price and it's lower than the regular price.
        """
        return self.sale_price is not None and self.sale_price < self.price
    
    @property
    def current_price(self):
        """
        Returns the current price (sale price if available, otherwise regular price).
        """
        if self.is_on_sale:
            return self.sale_price
        return self.price


class ProductImage(UUIDModel, TimestampedModel):
    """
    Product image model.
    """
    product = models.ForeignKey(
        Product, related_name='images', 
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to='products')
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _('Product Image')
        verbose_name_plural = _('Product Images')
        ordering = ['-is_primary', 'created_at']
    
    def __str__(self):
        return f"Image for {self.product.name}"


class Attribute(SluggedModel, TimestampedModel):
    """
    Product attribute model (e.g., Color, Size).
    """
    class Meta:
        verbose_name = _('Attribute')
        verbose_name_plural = _('Attributes')
    
    def __str__(self):
        return self.name


class AttributeValue(TimestampedModel):
    """
    Product attribute value model (e.g., Red, Large).
    """
    attribute = models.ForeignKey(
        Attribute, related_name='values', 
        on_delete=models.CASCADE
    )
    value = models.CharField(max_length=100)
    
    class Meta:
        verbose_name = _('Attribute Value')
        verbose_name_plural = _('Attribute Values')
        unique_together = ('attribute', 'value')
    
    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class ProductVariant(UUIDModel, TimestampedModel, PublishableModel):
    """
    Product variant model for products with options (e.g., different sizes/colors).
    """
    product = models.ForeignKey(
        Product, related_name='variants', 
        on_delete=models.CASCADE
    )
    sku = models.CharField(max_length=100, unique=True)
    price_adjustment = models.DecimalField(
        max_digits=10, decimal_places=2, 
        default=0.00
    )
    stock_qty = models.PositiveIntegerField(default=0)
    attributes = models.ManyToManyField(
        AttributeValue, 
        related_name='variants'
    )
    
    class Meta:
        verbose_name = _('Product Variant')
        verbose_name_plural = _('Product Variants')
    
    def __str__(self):
        attribute_values = ', '.join([str(attr) for attr in self.attributes.all()])
        return f"{self.product.name} - {attribute_values}"
    
    @property
    def price(self):
        """
        Returns the price of this variant (base product price + adjustment).
        """
        return self.product.price + self.price_adjustment
    
    @property
    def sale_price(self):
        """
        Returns the sale price if the product is on sale.
        """
        if self.product.sale_price:
            return self.product.sale_price + self.price_adjustment
        return None