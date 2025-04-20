# products/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from .models import Product, Category, AttributeValue
from .services.catalog import CatalogService
from django.core.paginator import Paginator


def catalog(request):
    """
    Main product catalog view.
    """
    # Get query parameters
    category_slug = request.GET.get('category')
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 12)
    sort = request.GET.get('sort', 'newest')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    on_sale = request.GET.get('on_sale') == 'true'
    in_stock = request.GET.get('in_stock') == 'true'
    
    # Get attribute filters
    attribute_filters = {}
    for key, value in request.GET.items():
        if key.startswith('attr_'):
            attribute_filters[key] = value
    
    # Build filters dictionary
    filters = {
        'sort': sort,
        'min_price': min_price,
        'max_price': max_price,
        'on_sale': on_sale,
        'in_stock': in_stock,
        **attribute_filters
    }
    
    # Get products
    paginator, current_page, queryset, has_filters = CatalogService.get_products_by_category(
        category_slug, page, per_page, **filters
    )
    
    # Get available filters
    category = None
    if category_slug:
        category = CatalogService.get_category_by_slug(category_slug)
    
    filter_options = CatalogService.get_available_filters(category)
    
    context = {
        'category': category,
        'products': current_page,
        'filters': filters,
        'has_filters': has_filters,
        'filter_options': filter_options,
        'paginator': paginator
    }
    
    return render(request, 'products/catalog.html', context)


def product_detail(request, slug):
    """
    Product detail view.
    """
    # Get the product
    product = CatalogService.get_product_by_slug(slug)
    
    if not product:
        messages.error(request, 'Product not found.')
        return redirect('products:catalog')
    
    # Get product variants
    variants = CatalogService.get_product_variants(product)
    
    # Get related products
    related_products = CatalogService.get_related_products(product)
    
    context = {
        'product': product,
        'variants': variants,
        'related_products': related_products
    }
    
    return render(request, 'products/detail.html', context)


def search(request):
    """
    Product search view.
    """
    query = request.GET.get('q', '')
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 12)
    
    # Search products
    paginator, current_page, queryset = CatalogService.search_products(query, page, per_page)
    
    context = {
        'query': query,
        'products': current_page,
        'result_count': queryset.count(),
        'paginator': paginator
    }
    
    return render(request, 'products/search.html', context)


def category_list(request):
    """
    Category listing view.
    """
    # Get all active parent categories
    categories = CatalogService.get_categories()
    
    context = {
        'categories': categories
    }
    
    return render(request, 'products/categories.html', context)


def category_detail(request, slug):
    """
    Category detail view.
    """
    # Get the category
    category = CatalogService.get_category_by_slug(slug)
    
    if not category:
        messages.error(request, 'Category not found.')
        return redirect('products:catalog')
    
    # Get query parameters
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 12)
    sort = request.GET.get('sort', 'newest')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    on_sale = request.GET.get('on_sale') == 'true'
    in_stock = request.GET.get('in_stock') == 'true'
    
    # Get attribute filters
    attribute_filters = {}
    for key, value in request.GET.items():
        if key.startswith('attr_'):
            attribute_filters[key] = value
    
    # Build filters dictionary
    filters = {
        'sort': sort,
        'min_price': min_price,
        'max_price': max_price,
        'on_sale': on_sale,
        'in_stock': in_stock,
        **attribute_filters
    }
    
    # Get products in this category
    paginator, current_page, queryset, has_filters = CatalogService.get_products_by_category(
        category.slug, page, per_page, **filters
    )
    
    # Get available filters
    filter_options = CatalogService.get_available_filters(category)
    
    context = {
        'category': category,
        'products': current_page,
        'filters': filters,
        'has_filters': has_filters,
        'filter_options': filter_options,
        'paginator': paginator
    }
    
    return render(request, 'products/category_detail.html', context)


def get_variant_price(request):
    """
    AJAX view for getting variant price.
    """
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Get the product and attribute values
        product_id = request.GET.get('product_id')
        attribute_values = {}
        
        for key, value in request.GET.items():
            if key.startswith('attr_'):
                attr_id = key.replace('attr_', '')
                attribute_values[attr_id] = value
        
        # Get the product
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found.'})
        
        # Get the variant
        variant = CatalogService.get_variant_by_attributes(product, attribute_values)
        
        if variant:
            # Return variant data
            return JsonResponse({
                'success': True,
                'price': variant.price,
                'sale_price': variant.sale_price,
                'in_stock': variant.stock_qty > 0,
                'stock_qty': variant.stock_qty,
                'sku': variant.sku,
                'id': str(variant.id)
            })
        
        # No variant found
        return JsonResponse({'error': 'Variant not found.'})
    
    # Not an AJAX request
    return JsonResponse({'error': 'Invalid request.'})
