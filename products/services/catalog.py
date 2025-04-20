# products/services/catalog.py
class ProductService:
    @staticmethod
    def get_featured_products(limit=8):
        # Business logic for getting featured products
        return Product.objects.filter(is_featured=True)[:limit]
    
    @staticmethod
    def get_products_by_category(category_slug, **filters):
        # Logic for filtering products
        return Product.objects.filter(category__slug=category_slug, **filters)