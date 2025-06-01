from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from core.models import TimestampedModel, SluggedModel, PublishableModel, SEOModel


class Category(SluggedModel, TimestampedModel, PublishableModel, SEOModel):
    """
    Product category model.
    """

    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="categories", blank=True, null=True)

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("products:category_detail", args=[self.slug])


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

    def physical(self):
        """Returns only physical products"""
        return self.active().filter(product_type="physical")

    def digital(self):
        """Returns only digital products"""
        return self.active().filter(product_type="digital")

    def in_stock(self):
        """Returns products that are in stock"""
        return self.active().filter(in_stock=True)

    def get_by_category(self, category_slug):
        """
        Returns all products in the given category.
        """
        return self.active().filter(category__slug=category_slug)


class Product(SluggedModel, TimestampedModel, PublishableModel, SEOModel):
    """
    Product model supporting both physical and digital products.
    """

    # Product type choices
    PRODUCT_TYPES = [
        ("physical", "Physical Product"),
        ("digital", "Digital Download"),
    ]

    category = models.ForeignKey(
        Category, related_name="products", on_delete=models.CASCADE
    )

    # Basic product info
    product_type = models.CharField(
        max_length=20,
        choices=PRODUCT_TYPES,
        default="physical",
        help_text="Type of product: physical item or digital download",
    )
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )

    # Physical product fields
    requires_shipping = models.BooleanField(
        default=True, help_text="Whether this product needs shipping"
    )
    weight = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Weight in kg for shipping calculations",
    )
    dimensions = models.CharField(
        max_length=100, blank=True, help_text="Dimensions for shipping (L x W x H)"
    )

    # Digital product fields
    digital_file = models.FileField(
        upload_to="digital_products/",
        null=True,
        blank=True,
        help_text="File to be downloaded (for digital products)",
    )
    download_limit = models.PositiveIntegerField(
        default=5,
        null=True,
        blank=True,
        help_text="Maximum number of downloads allowed per purchase",
    )
    download_expiry_days = models.PositiveIntegerField(
        default=30,
        null=True,
        blank=True,
        help_text="Number of days download link remains valid",
    )

    # Stock and availability
    is_featured = models.BooleanField(default=False)
    in_stock = models.BooleanField(default=True)
    stock_qty = models.PositiveIntegerField(
        default=0, help_text="Stock quantity (ignored for digital products)"
    )

    # Image fields
    main_image = models.ImageField(upload_to="products")

    # SEO fields (inherited from SEOModel)

    objects = ProductManager()

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["is_featured"]),
            models.Index(fields=["in_stock"]),
            models.Index(fields=["product_type"]),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("products:product_detail", args=[self.slug])

    def save(self, *args, **kwargs):
        """Override save to set defaults based on product type"""
        if self.product_type == "digital":
            # Digital products don't need shipping
            self.requires_shipping = False
            # Digital products are always "in stock"
            self.in_stock = True
            # Clear physical product fields
            self.weight = None
            self.dimensions = ""
        elif self.product_type == "physical":
            # Physical products don't have digital fields
            self.digital_file = None
            self.download_limit = None
            self.download_expiry_days = None
            self.requires_shipping = True

        super().save(*args, **kwargs)

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

    @property
    def effective_price(self):
        """Returns current price for API serialization"""
        return self.current_price

    @property
    def is_digital(self):
        """Returns True if this is a digital product"""
        return self.product_type == "digital"

    @property
    def is_downloadable(self):
        """Returns True if product has a digital file"""
        return self.is_digital and bool(self.digital_file)

    @property
    def is_unlimited_download(self):
        """Returns True if digital product has unlimited downloads"""
        return self.is_digital and (
            self.download_limit is None or self.download_limit <= 0
        )

    def get_download_file(self, variant=None):
        """Gets the appropriate download file for this product/variant"""
        if variant and variant.digital_file:
            return variant.digital_file
        return self.digital_file


class ProductImage(TimestampedModel):
    """
    Product image model.
    """

    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="products")
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Product Image")
        verbose_name_plural = _("Product Images")
        ordering = ["-is_primary", "created_at"]

    def __str__(self):
        return f"Image for {self.product.name}"


class Attribute(SluggedModel, TimestampedModel):
    """
    Product attribute model (e.g., Color, Size).
    """

    class Meta:
        verbose_name = _("Attribute")
        verbose_name_plural = _("Attributes")

    def __str__(self):
        return self.name


class AttributeValue(TimestampedModel):
    """
    Product attribute value model (e.g., Red, Large).
    """

    attribute = models.ForeignKey(
        Attribute, related_name="values", on_delete=models.CASCADE
    )
    value = models.CharField(max_length=100)

    class Meta:
        verbose_name = _("Attribute Value")
        verbose_name_plural = _("Attribute Values")
        unique_together = ("attribute", "value")

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class ProductVariant(TimestampedModel, PublishableModel):
    """
    Product variant model for products with options.
    """

    product = models.ForeignKey(
        Product, related_name="variants", on_delete=models.CASCADE
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Variant name (e.g., 'Red - Large', 'PDF Version')",
    )
    sku = models.CharField(
        max_length=100, blank=True, help_text="SKU for this specific variant"
    )
    price_adjustment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Price difference from base product price",
    )
    stock_qty = models.PositiveIntegerField(default=0)

    # Digital variant support
    digital_file = models.FileField(
        upload_to="digital_variants/",
        null=True,
        blank=True,
        help_text="Specific file for this variant (overrides product file)",
    )

    # Attributes for variants
    attributes = models.ManyToManyField(
        AttributeValue, related_name="variants", blank=True
    )

    class Meta:
        verbose_name = _("Product Variant")
        verbose_name_plural = _("Product Variants")
        unique_together = [("product", "sku")]  # SKU unique per product

    def __str__(self):
        if self.name:
            return f"{self.product.name} - {self.name}"
        attribute_values = ", ".join([str(attr) for attr in self.attributes.all()])
        return (
            f"{self.product.name} - {attribute_values}"
            if attribute_values
            else self.product.name
        )

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

    @property
    def effective_digital_file(self):
        """Returns the digital file for this variant or falls back to product file"""
        return self.digital_file or self.product.digital_file
