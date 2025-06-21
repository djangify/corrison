# cart/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import transaction
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from products.models import Product
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
        """Get or create cart using Django sessions with improved merging."""
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()

        session_key = request.session.session_key
        logger.info(f"Getting cart for session: {session_key}, User: {request.user}")

        with transaction.atomic():
            cart = None

            # For authenticated users
            if request.user.is_authenticated:
                # First, try to get user's active cart
                user_cart = (
                    Cart.objects.filter(user=request.user, is_active=True)
                    .order_by("-updated_at")
                    .first()
                )

                # Also check for session cart
                session_cart = (
                    Cart.objects.filter(session_key=session_key, is_active=True)
                    .exclude(user=request.user)
                    .first()
                )

                if user_cart and session_cart:
                    # Merge session cart into user cart
                    logger.info(
                        f"Merging session cart {session_cart.id} into user cart {user_cart.id}"
                    )
                    user_cart.merge_with(session_cart)
                    cart = user_cart
                elif user_cart:
                    # Just use user cart, update session key
                    cart = user_cart
                    if cart.session_key != session_key:
                        cart.session_key = session_key
                        cart.save(update_fields=["session_key", "updated_at"])
                elif session_cart:
                    # Assign session cart to user
                    logger.info(
                        f"Assigning session cart {session_cart.id} to user {request.user}"
                    )
                    session_cart.user = request.user
                    session_cart.save(update_fields=["user", "updated_at"])
                    cart = session_cart
                else:
                    # Create new cart for user
                    cart = Cart.objects.create(
                        user=request.user, session_key=session_key, is_active=True
                    )
                    logger.info(f"Created new cart {cart.id} for user {request.user}")

            else:
                # For anonymous users, get or create session cart
                try:
                    cart = Cart.objects.get(
                        session_key=session_key, is_active=True, user__isnull=True
                    )
                except Cart.DoesNotExist:
                    cart = Cart.objects.create(session_key=session_key, is_active=True)
                    logger.info(f"Created new session cart {cart.id}")
                except Cart.MultipleObjectsReturned:
                    # Clean up duplicate session carts
                    carts = Cart.objects.filter(
                        session_key=session_key, is_active=True, user__isnull=True
                    ).order_by("-updated_at")

                    # Keep the most recent one with items
                    cart = None
                    for c in carts:
                        if c.items.exists() and not cart:
                            cart = c
                        else:
                            c.is_active = False
                            c.save()

                    if not cart:
                        cart = carts.first()
                        cart.is_active = True
                        cart.save()

            logger.info(f"Returning cart {cart.id} with {cart.items.count()} items")
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

        # Update cart timestamp
        cart.save(update_fields=["updated_at"])

        # Return updated cart
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
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

            # Update cart timestamp
            cart.save(update_fields=["updated_at"])

            serializer = CartSerializer(cart)
            return Response(serializer.data)
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Item not found in cart"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["post"])
    def remove_item(self, request):
        """Remove item from cart."""
        cart = self.get_cart_from_request(request)
        item_id = request.data.get("item_id")

        try:
            cart_item = cart.items.get(id=item_id)
            cart_item.delete()

            # Update cart timestamp
            cart.save(update_fields=["updated_at"])

            serializer = CartSerializer(cart)
            return Response(serializer.data)
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Item not found in cart"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["post"])
    def clear(self, request):
        """Clear all items from cart."""
        cart = self.get_cart_from_request(request)
        cart.clear()

        # Update cart timestamp
        cart.save(update_fields=["updated_at"])

        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def merge_session_cart(self, request):
        """Explicitly merge session cart with user cart after login."""
        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # This will automatically handle merging
        cart = self.get_cart_from_request(request)
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

        # Update cart timestamp
        cart.save(update_fields=["updated_at"])

        serializer = self.get_serializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update cart item quantity."""
        cart_item = self.get_object()
        quantity = int(request.data.get("quantity", 1))

        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()

            # Update cart timestamp
            cart_item.cart.save(update_fields=["updated_at"])

            serializer = self.get_serializer(cart_item)
            return Response(serializer.data)
        else:
            cart = cart_item.cart
            cart_item.delete()

            # Update cart timestamp
            cart.save(update_fields=["updated_at"])

            return Response(status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, *args, **kwargs):
        """Remove item from cart."""
        cart_item = self.get_object()
        cart = cart_item.cart
        cart_item.delete()

        # Update cart timestamp
        cart.save(update_fields=["updated_at"])

        return Response(status=status.HTTP_204_NO_CONTENT)
