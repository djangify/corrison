# products/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from .models import Product
from .services.catalog import CatalogService
from django.core.paginator import Paginator


def catalog(request):
    """
    Main product catalog view.
    """
    # Get query parameters
    category_slug = request.GET.get("category")
    page = request.GET.get("page", 1)
    per_page = request.GET.get("per_page", 12)
    sort = request.GET.get("sort", "newest")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    on_sale = request.GET.get("on_sale") == "true"
    in_stock = request.GET.get("in_stock") == "true"
    product_type = request.GET.get("product_type")  # Add product type filter

    # Get attribute filters
    attribute_filters = {}
    for key, value in request.GET.items():
        if key.startswith("attr_"):
            attribute_filters[key] = value

    # Build filters dictionary
    filters = {
        "sort": sort,
        "min_price": min_price,
        "max_price": max_price,
        "on_sale": on_sale,
        "in_stock": in_stock,
        "product_type": product_type,  # Add product type to filters
        **attribute_filters,
    }

    # Get products
    paginator, current_page, queryset, has_filters = (
        CatalogService.get_products_by_category(
            category_slug, page, per_page, **filters
        )
    )

    # Get available filters
    category = None
    if category_slug:
        category = CatalogService.get_category_by_slug(category_slug)

    filter_options = CatalogService.get_available_filters(category)

    context = {
        "category": category,
        "products": current_page,
        "filters": filters,
        "has_filters": has_filters,
        "filter_options": filter_options,
        "paginator": paginator,
    }

    return render(request, "products/catalog.html", context)


def product_detail(request, slug):
    """
    Product detail view.
    """
    # Get the product
    product = CatalogService.get_product_by_slug(slug)

    if not product:
        messages.error(request, "Product not found.")
        return redirect("products:catalog")

    # Get product variants
    variants = CatalogService.get_product_variants(product)

    # Get related products
    related_products = CatalogService.get_related_products(product)

    # Add digital product context
    is_digital = product.is_digital
    is_downloadable = product.is_downloadable

    context = {
        "product": product,
        "variants": variants,
        "related_products": related_products,
        "is_digital": is_digital,  # Add digital product flags
        "is_downloadable": is_downloadable,
        "requires_shipping": product.requires_shipping,
    }

    return render(request, "products/detail.html", context)


def search(request):
    """
    Product search view.
    """
    query = request.GET.get("q", "")
    page = request.GET.get("page", 1)
    per_page = request.GET.get("per_page", 12)
    product_type = request.GET.get("product_type")  # Add product type filter to search

    # Search products
    paginator, current_page, queryset = CatalogService.search_products(
        query, page, per_page, product_type=product_type
    )

    context = {
        "query": query,
        "products": current_page,
        "result_count": queryset.count(),
        "paginator": paginator,
        "product_type": product_type,  # Add product type to context
    }

    return render(request, "products/search.html", context)


def category_list(request):
    """
    Category listing view.
    """
    # Get all active parent categories
    categories = CatalogService.get_categories()

    context = {"categories": categories}

    return render(request, "products/categories.html", context)


def category_detail(request, slug):
    """
    Category detail view.
    """
    # Get the category
    category = CatalogService.get_category_by_slug(slug)

    if not category:
        messages.error(request, "Category not found.")
        return redirect("products:catalog")

    # Get query parameters
    page = request.GET.get("page", 1)
    per_page = request.GET.get("per_page", 12)
    sort = request.GET.get("sort", "newest")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    on_sale = request.GET.get("on_sale") == "true"
    in_stock = request.GET.get("in_stock") == "true"
    product_type = request.GET.get("product_type")  # Add product type filter

    # Get attribute filters
    attribute_filters = {}
    for key, value in request.GET.items():
        if key.startswith("attr_"):
            attribute_filters[key] = value

    # Build filters dictionary
    filters = {
        "sort": sort,
        "min_price": min_price,
        "max_price": max_price,
        "on_sale": on_sale,
        "in_stock": in_stock,
        "product_type": product_type,  # Add product type to filters
        **attribute_filters,
    }

    # Get products in this category
    paginator, current_page, queryset, has_filters = (
        CatalogService.get_products_by_category(
            category.slug, page, per_page, **filters
        )
    )

    # Get available filters
    filter_options = CatalogService.get_available_filters(category)

    context = {
        "category": category,
        "products": current_page,
        "filters": filters,
        "has_filters": has_filters,
        "filter_options": filter_options,
        "paginator": paginator,
    }

    return render(request, "products/category_detail.html", context)


def get_variant_price(request):
    """
    AJAX view for getting variant price.
    """
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        # Get the product and attribute values
        product_id = request.GET.get("product_id")
        attribute_values = {}

        for key, value in request.GET.items():
            if key.startswith("attr_"):
                attr_id = key.replace("attr_", "")
                attribute_values[attr_id] = value

        # Get the product - product_id is now an integer
        try:
            product_id = int(product_id)  # Convert to integer
            product = Product.objects.get(id=product_id)
        except (Product.DoesNotExist, ValueError, TypeError):
            return JsonResponse({"error": "Product not found."})

        # Get the variant
        variant = CatalogService.get_variant_by_attributes(product, attribute_values)

        if variant:
            # Return variant data - variant.id is now an integer
            return JsonResponse(
                {
                    "success": True,
                    "price": variant.price,
                    "sale_price": variant.sale_price,
                    "in_stock": variant.stock_qty > 0,
                    "stock_qty": variant.stock_qty,
                    "sku": variant.sku,
                    "id": variant.id,  # No longer need str() conversion
                    "is_digital": variant.product.is_digital,  # Add digital product info
                    "requires_shipping": variant.product.requires_shipping,
                }
            )

        # No variant found
        return JsonResponse({"error": "Variant not found."})

    # Not an AJAX request
    return JsonResponse({"error": "Invalid request."})


def digital_products(request):
    """
    View for digital products only.
    """
    page = request.GET.get("page", 1)
    per_page = request.GET.get("per_page", 12)
    sort = request.GET.get("sort", "newest")

    # Build filters for digital products only
    filters = {
        "sort": sort,
        "product_type": "digital",
    }

    # Get digital products
    paginator, current_page, queryset, has_filters = (
        CatalogService.get_products_by_category(None, page, per_page, **filters)
    )

    context = {
        "products": current_page,
        "paginator": paginator,
        "page_title": "Digital Downloads",
        "is_digital_only": True,
    }

    return render(request, "products/digital_products.html", context)


def physical_products(request):
    """
    View for physical products only.
    """
    page = request.GET.get("page", 1)
    per_page = request.GET.get("per_page", 12)
    sort = request.GET.get("sort", "newest")

    # Build filters for physical products only
    filters = {
        "sort": sort,
        "product_type": "physical",
    }

    # Get physical products
    paginator, current_page, queryset, has_filters = (
        CatalogService.get_products_by_category(None, page, per_page, **filters)
    )

    context = {
        "products": current_page,
        "paginator": paginator,
        "page_title": "Physical Products",
        "is_physical_only": True,
    }

    return render(request, "products/physical_products.html", context)
