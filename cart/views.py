# cart/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import transaction
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from products.models import Product
from django.views.decorators.csrf import csrf_exempt

import logging

logger = logging.getLogger(__name__)


class CartViewSet(viewsets.ViewSet):
    """
    Cart management using Django sessions.
    No authentication required - carts are session-based.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get_cart_from_request(self, request):
        """Get or create cart using Django sessions."""
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()

        session_key = request.session.session_key

        with transaction.atomic():
            # For authenticated users, try to get their cart first
            if request.user.is_authenticated:
                # Try to get user's active cart
                cart = (
                    Cart.objects.filter(user=request.user, is_active=True)
                    .order_by("-updated_at")
                    .first()
                )

                if cart:
                    # Update session_key if needed
                    if cart.session_key != session_key:
                        cart.session_key = session_key
                        cart.save(update_fields=["session_key"])
                    return cart

            # Try to get cart by session key
            try:
                cart = Cart.objects.get(session_key=session_key, is_active=True)

                # If user is authenticated and cart has no user, assign it
                if request.user.is_authenticated and not cart.user:
                    cart.user = request.user
                    cart.save(update_fields=["user"])

            except Cart.DoesNotExist:
                # Use get_or_create to prevent race conditions
                cart, created = Cart.objects.get_or_create(
                    session_key=session_key,
                    is_active=True,
                    defaults={
                        "user": request.user if request.user.is_authenticated else None,
                        "is_active": True,
                    },
                )

            except Cart.MultipleObjectsReturned:
                # Multiple carts found - consolidate them
                carts = Cart.objects.filter(
                    session_key=session_key, is_active=True
                ).order_by("-created_at")

                # Prefer cart with items
                cart_with_items = None
                for c in carts:
                    if c.items.exists():
                        cart_with_items = c
                        break

                if cart_with_items:
                    cart = cart_with_items
                else:
                    cart = carts.first()

                # Deactivate all other carts
                carts.exclude(id=cart.id).update(is_active=False)

            # If user is authenticated, check for other carts to merge
            if request.user.is_authenticated and cart.user == request.user:
                other_carts = Cart.objects.filter(
                    user=request.user, is_active=True
                ).exclude(id=cart.id)

                for other_cart in other_carts:
                    cart.merge_with(other_cart)

            return cart

    def list(self, request):
        """Get the current cart."""
        cart = self.get_cart_from_request(request)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Get cart - redirects to list for session-based cart."""
        return self.list(request)

    @action(detail=False, methods=["post"])
    def add(self, request):
        """Add item to cart."""
        cart = self.get_cart_from_request(request)

        product_id = request.data.get("product_id") or request.data.get("product")
        quantity = int(request.data.get("quantity", 1))

        if not product_id:
            return Response(
                {"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product = Product.objects.get(pk=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Get or create cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, defaults={"quantity": 0}
        )

        # Update quantity
        cart_item.quantity += quantity
        cart_item.save()

        # Return updated cart
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    @csrf_exempt
    def update_item(self, request):
        """Update cart item quantity."""
        cart = self.get_cart_from_request(request)
        item_id = request.data.get("item_id")
        quantity = int(request.data.get("quantity", 1))

        try:
            cart_item = cart.items.get(id=item_id)
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
            else:
                cart_item.delete()

            serializer = CartSerializer(cart)
            return Response(serializer.data)
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Item not found in cart"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["post"])
    @csrf_exempt
    def remove_item(self, request):
        """Remove item from cart."""
        cart = self.get_cart_from_request(request)
        item_id = request.data.get("item_id")

        try:
            cart_item = cart.items.get(id=item_id)
            cart_item.delete()

            serializer = CartSerializer(cart)
            return Response(serializer.data)
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Item not found in cart"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["post"])
    @csrf_exempt
    def clear(self, request):
        """Clear all items from cart."""
        cart = self.get_cart_from_request(request)
        cart.clear()

        serializer = CartSerializer(cart)
        return Response(serializer.data)


class CartItemViewSet(viewsets.ModelViewSet):
    """
    Cart item management.
    Items are accessed through the cart they belong to.
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = CartItemSerializer

    def get_cart(self):
        """Get cart from request."""
        cart_viewset = CartViewSet()
        return cart_viewset.get_cart_from_request(self.request)

    def get_queryset(self):
        """Get cart items for current session."""
        cart = self.get_cart()
        return CartItem.objects.filter(cart=cart).select_related("product", "variant")

    def create(self, request, *args, **kwargs):
        """Add item to cart."""
        cart = self.get_cart()

        product_id = request.data.get("product")
        quantity = int(request.data.get("quantity", 1))

        try:
            product = Product.objects.get(pk=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Get or create cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, defaults={"quantity": 0}
        )

        # Update quantity
        cart_item.quantity += quantity
        cart_item.save()

        serializer = self.get_serializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update cart item quantity."""
        cart_item = self.get_object()
        quantity = int(request.data.get("quantity", 1))

        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            serializer = self.get_serializer(cart_item)
            return Response(serializer.data)
        else:
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, *args, **kwargs):
        """Remove item from cart."""
        cart_item = self.get_object()
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
