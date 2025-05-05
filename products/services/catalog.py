# products/services/catalog.py
from django.db.models import Count, Q
from django.core.paginator import Paginator
from products.models import Product, Category, ProductVariant, AttributeValue


class CatalogService:
    """
    Service class for handling catalog related operations.
    This separates business logic from views.
    """
    
    @staticmethod
    def get_featured_products(limit=8):
        """
        Get featured products.
        
        Args:
            limit (int): Number of products to return
            
        Returns:
            QuerySet: A queryset of featured products
        """
        return Product.objects.active().filter(
            is_featured=True
        ).select_related('category').prefetch_related('images')[:limit]
    
    @staticmethod
    def get_new_arrivals(limit=8):
        """
        Get newly added products.
        
        Args:
            limit (int): Number of products to return
            
        Returns:
            QuerySet: A queryset of new products
        """
        return Product.objects.active().order_by(
            '-created_at'
        ).select_related('category').prefetch_related('images')[:limit]
    
    @staticmethod
    def get_on_sale_products(limit=8):
        """
        Get products that are on sale.
        
        Args:
            limit (int): Number of products to return
            
        Returns:
            QuerySet: A queryset of sale products
        """
        return Product.objects.active().filter(
            sale_price__isnull=False
        ).select_related('category').prefetch_related('images')[:limit]
    
    @staticmethod
    def get_product_by_slug(slug):
        """
        Get a specific product by slug.
        
        Args:
            slug (str): Product slug
            
        Returns:
            Product: The product or None if not found
        """
        try:
            return Product.objects.active().select_related(
                'category'
            ).prefetch_related(
                'images', 
                'variants', 
                'variants__attributes',
                'variants__attributes__attribute'
            ).get(slug=slug)
        except Product.DoesNotExist:
            return None
    
    @staticmethod
    def get_related_products(product, limit=4):
        """
        Get products related to a specific product.
        
        Args:
            product (Product): The product to find related products for
            limit (int): Number of products to return
            
        Returns:
            QuerySet: A queryset of related products
        """
        # Get products in the same category, excluding the current product
        return Product.objects.active().filter(
            category=product.category
        ).exclude(
            id=product.id
        ).select_related('category').prefetch_related('images')[:limit]
    
    @staticmethod
    def get_product_variants(product):
        """
        Get all variants for a product.
        
        Args:
            product (Product): The product to get variants for
            
        Returns:
            QuerySet: A queryset of product variants
        """
        return ProductVariant.objects.filter(
            product=product, 
            is_active=True
        ).prefetch_related(
            'attributes', 
            'attributes__attribute'
        )
    
    @staticmethod
    def get_variant_by_attributes(product, attribute_values):
        """
        Get a product variant by attribute values.
        
        Args:
            product (Product): The product
            attribute_values (dict): Dictionary of attribute_id: value_id
            
        Returns:
            ProductVariant: The product variant or None if not found
        """
        variants = ProductVariant.objects.filter(product=product, is_active=True)
        
        for attr_id, value_id in attribute_values.items():
            variants = variants.filter(attributes__id=value_id)
        
        return variants.first()
    
    @staticmethod
    def get_categories(parent=None, include_inactive=False):
        """
        Get categories, optionally filtered by parent.
        
        Args:
            parent (Category, optional): Parent category
            include_inactive (bool): Whether to include inactive categories
            
        Returns:
            QuerySet: A queryset of categories
        """
        queryset = Category.objects.all()
        
        if not include_inactive:
            queryset = queryset.filter(is_active=True)
            
        if parent is not None:
            queryset = queryset.filter(parent=parent)
        else:
            queryset = queryset.filter(parent__isnull=True)
            
        return queryset.prefetch_related('children')
    
    @staticmethod
    def get_category_by_slug(slug):
        """
        Get a specific category by slug.
        
        Args:
            slug (str): Category slug
            
        Returns:
            Category: The category or None if not found
        """
        try:
            return Category.objects.filter(
                is_active=True
            ).prefetch_related('children').get(slug=slug)
        except Category.DoesNotExist:
            return None
    
    @staticmethod
    def get_products_by_category(category_slug, page=1, per_page=12, **filters):
        """
        Get products in a specific category with pagination.
        
        Args:
            category_slug (str): Category slug
            page (int): Page number
            per_page (int): Number of products per page
            **filters: Additional filters
            
        Returns:
            tuple: (Paginator, Page, QuerySet, bool) - paginator, current page, queryset, has_filters
        """
        has_filters = bool(filters)
        
        # Start with all active products
        queryset = Product.objects.active().select_related(
            'category'
        ).prefetch_related('images')
        
        # Filter by category if provided
        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug, is_active=True)
                # Get all child categories as well
                categories = [category]
                children = category.children.filter(is_active=True)
                categories.extend(children)
                
                queryset = queryset.filter(category__in=categories)
            except Category.DoesNotExist:
                queryset = queryset.none()
        
        # Apply price filter
        min_price = filters.get('min_price')
        max_price = filters.get('max_price')
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
            
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Apply sort order
        sort = filters.get('sort', 'newest')
        
        if sort == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort == 'price_low':
            queryset = queryset.order_by('price')
        elif sort == 'price_high':
            queryset = queryset.order_by('-price')
        elif sort == 'name_asc':
            queryset = queryset.order_by('name')
        elif sort == 'name_desc':
            queryset = queryset.order_by('-name')
        else:
            queryset = queryset.order_by('-created_at')
        
        # Apply other filters
        if filters.get('on_sale'):
            queryset = queryset.filter(sale_price__isnull=False)
            
        if filters.get('in_stock'):
            queryset = queryset.filter(in_stock=True, stock_qty__gt=0)
            
        # Apply attribute filters
        attribute_filters = {k: v for k, v in filters.items() if k.startswith('attr_')}
        
        for attr_key, attr_value in attribute_filters.items():
            attr_id = attr_key.replace('attr_', '')
            queryset = queryset.filter(
                variants__attributes__attribute_id=attr_id,
                variants__attributes__value=attr_value
            ).distinct()
        
        # Paginate the results
        paginator = Paginator(queryset, per_page)
        current_page = paginator.get_page(page)
        
        return paginator, current_page, queryset, has_filters
    
    @staticmethod
    def search_products(query, page=1, per_page=12):
        """
        Search for products.
        
        Args:
            query (str): Search query
            page (int): Page number
            per_page (int): Number of products per page
            
        Returns:
            tuple: (Paginator, Page, QuerySet) - paginator, current page, queryset
        """
        if not query:
            queryset = Product.objects.none()
        else:
            queryset = Product.objects.active().filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query) |
                Q(sku__icontains=query) |
                Q(category__name__icontains=query)
            ).select_related('category').prefetch_related('images').distinct()
        
        # Paginate the results
        paginator = Paginator(queryset, per_page)
        current_page = paginator.get_page(page)
        
        return paginator, current_page, queryset
    
    @staticmethod
    def get_available_filters(category=None):
        """
        Get available filters for product filtering.
        
        Args:
            category (Category, optional): Category to filter by
            
        Returns:
            dict: Dictionary of available filters
        """
        # Start with all active products
        queryset = Product.objects.active()
        
        # Filter by category if provided
        if category:
            # Get all child categories as well
            categories = [category]
            children = category.children.filter(is_active=True)
            categories.extend(children)
            
            queryset = queryset.filter(category__in=categories)
        
        # Get min and max prices
        try:
            min_price = queryset.order_by('price').first().price
            max_price = queryset.order_by('-price').first().price
        except AttributeError:
            min_price = 0
            max_price = 0
        
        # Get on sale count
        on_sale_count = queryset.filter(sale_price__isnull=False).count()
        
        # Get in stock count
        in_stock_count = queryset.filter(in_stock=True, stock_qty__gt=0).count()
        
        # Get available attributes
        attribute_values = AttributeValue.objects.filter(
            variants__product__in=queryset
        ).select_related('attribute').values(
            'attribute__id', 'attribute__name', 'value'
        ).annotate(
            product_count=Count('variants__product', distinct=True)
        )
        
        # Organize attribute values by attribute
        attributes = {}
        for av in attribute_values:
            attr_id = av['attribute__id']
            attr_name = av['attribute__name']
            
            if attr_id not in attributes:
                attributes[attr_id] = {
                    'id': attr_id,
                    'name': attr_name,
                    'values': []
                }
            
            attributes[attr_id]['values'].append({
                'value': av['value'],
                'product_count': av['product_count']
            })
        
        return {
            'price_range': {
                'min': min_price,
                'max': max_price
            },
            'on_sale': {
                'count': on_sale_count
            },
            'in_stock': {
                'count': in_stock_count
            },
            'attributes': list(attributes.values())
        }
    