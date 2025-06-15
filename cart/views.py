# cart/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from .utils import CartTokenManager
from products.models import Product, ProductVariant
from django.shortcuts import get_object_or_404
import logging

logger = logging.getLogger(__name__)


class CartViewSet(viewsets.ViewSet):  # CHANGED: GenericViewSet → ViewSet
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_cart_from_request(self, request):
        """
        Get or create cart - simplified for digital products.
        """
        # Try to get token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        cart_token = None

        if auth_header.startswith("Bearer "):
            cart_token = auth_header.split(" ")[1]
            # Validate token format
            if not CartTokenManager.is_valid_token(cart_token):
                cart_token = None

        # Get cart by token
        cart = None
        if cart_token:
            try:
                cart = Cart.objects.filter(token=cart_token, is_active=True).first()
            except Exception as e:
                logger.error(f"Error finding cart with token: {e}")
                cart = None

        # If no cart found and user is authenticated, get user's cart
        if not cart and request.user.is_authenticated:
            try:
                cart = Cart.objects.filter(user=request.user, is_active=True).first()
            except Exception as e:
                logger.error(f"Error finding user cart: {e}")

        # Create new cart if needed
        if not cart:
            try:
                cart = Cart.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    token=CartTokenManager.generate_cart_token(),
                )
            except Exception as e:
                logger.error(f"Error creating cart: {e}")
                return None

        # Ensure cart has a token
        if not cart.token:
            cart.token = CartTokenManager.generate_cart_token()
            cart.save()

        return cart

    def list(self, request):
        """
        Get the current cart.
        """
        cart = self.get_cart_from_request(request)
        if not cart:
            return Response(
                {"error": "Failed to create cart"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = CartSerializer(cart)

        # Add token to response
        data = serializer.data
        data["token"] = cart.token

        return Response(data)

    @action(detail=False, methods=["post"])
    def clear(self, request):
        """
        Clear all items from cart.
        """
        cart = self.get_cart_from_request(request)
        if not cart:
            return Response(
                {"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND
            )

        cart.clear()

        serializer = CartSerializer(cart)
        data = serializer.data
        data["token"] = cart.token

        return Response(data)


# CartItemViewSet stays the same - it already works with ModelViewSet
class CartItemViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = CartItemSerializer

    def get_queryset(self):
        cart = self.get_cart_from_request(self.request)
        if not cart:
            return CartItem.objects.none()
        return CartItem.objects.filter(cart=cart)

    def get_cart_from_request(self, request):
        """
        Get cart from request using CartViewSet's method.
        """
        cart_viewset = CartViewSet()
        return cart_viewset.get_cart_from_request(request)

    def create(self, request, *args, **kwargs):
        """
        Add item to cart - simplified for digital products.
        """
        cart = self.get_cart_from_request(request)
        if not cart:
            return Response(
                {"error": "Failed to access cart"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        product_id = request.data.get("product")
        variant_id = request.data.get("variant")
        quantity = request.data.get("quantity", 1)

        # Convert and validate product_id
        try:
            product_id = int(product_id)
            quantity = int(quantity)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid product ID or quantity format"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate product exists
        try:
            product = get_object_or_404(Product, pk=product_id, is_active=True)
        except Exception as e:
            logger.error(f"Product not found: {product_id}, error: {e}")
            return Response(
                {"error": "Product not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Handle variant if provided
        variant = None
        if variant_id:
            try:
                variant_id = int(variant_id)
                variant = get_object_or_404(
                    ProductVariant, pk=variant_id, product=product, is_active=True
                )
            except (ValueError, TypeError):
                return Response(
                    {"error": "Invalid variant ID format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Exception as e:
                logger.error(f"Variant not found: {variant_id}, error: {e}")
                return Response(
                    {"error": "Variant not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # Digital products: no stock checking needed
        # Check if item already exists in cart
        try:
            cart_item = CartItem.objects.get(
                cart=cart, product=product, variant=variant
            )
            # Update quantity
            cart_item.quantity += quantity
            cart_item.save()
        except CartItem.DoesNotExist:
            # Create new item
            cart_item = CartItem.objects.create(
                cart=cart, product=product, variant=variant, quantity=quantity
            )
        except Exception as e:
            logger.error(f"Error updating cart item: {e}")
            return Response(
                {"error": "Failed to update cart"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = self.get_serializer(cart_item)

        # Include cart token in response
        response_data = serializer.data
        response_data["cart_token"] = cart.token

        return Response(response_data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        Update cart item quantity - no stock checking for digital products.
        """
        cart_item = self.get_object()

        try:
            quantity = int(request.data.get("quantity", 1))
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid quantity format"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Digital products: no stock validation needed
        cart_item.quantity = quantity
        cart_item.save()

        serializer = self.get_serializer(cart_item)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Remove item from cart.
        """
        cart_item = self.get_object()
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
