# cart/services/cart_manager.py
from ..models import Cart, CartItem
from ..utils import CartTokenManager


class CartService:
    """
    Simplified cart service for digital products only.
    No more JWT complexity, no physical product logic.
    """

    @staticmethod
    def get_cart_from_token(cart_token):
        """
        Get cart by simple UUID token.
        """
        if not cart_token or not CartTokenManager.is_valid_token(cart_token):
            return None

        return Cart.objects.filter(token=cart_token, is_active=True).first()

    # Update the get_cart_data method in cart/services/cart_manager.py

    @staticmethod
    def get_cart_data(request, cart_token=None):
        """
        Get cart data - simplified for digital products only.
        """
        cart = None

        # Try to get cart token from Authorization header
        if not cart_token:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                cart_token = auth_header.split(" ")[1]

        # Get cart by token
        if cart_token:
            cart = CartService.get_cart_from_token(cart_token)

        # If no cart found and user is authenticated, get user's cart
        if not cart and request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user, is_active=True).first()

        # Create new cart if needed
        if not cart:
            cart = Cart.objects.create(
                user=request.user if request.user.is_authenticated else None,
                token=CartTokenManager.generate_cart_token(),
            )

        # Ensure cart has a token
        if not cart.token:
            cart.token = CartTokenManager.generate_cart_token()
            cart.save()

        # Get cart items
        items = cart.items.select_related("product", "variant").all()

        # Calculate subtotal safely
        subtotal = cart.subtotal if cart.subtotal is not None else 0.0

        return {
            "cart": cart,
            "items": items,
            "subtotal": float(subtotal),  # Ensure it's a float
            "item_count": cart.total_items,
            "cart_token": cart.token,
            # Digital-only flags (always true for digital)
            "has_digital_items": True,
            "has_physical_items": False,
            "is_digital_only": True,
            "requires_shipping": False,
        }

    @staticmethod
    def add_to_cart(cart_token, product, variant=None, quantity=1, user=None):
        """
        Add digital product to cart - simplified, no stock checking.
        """
        # Get or create cart
        cart = None
        if cart_token:
            cart = CartService.get_cart_from_token(cart_token)

        if not cart:
            cart = Cart.objects.create(
                user=user, token=CartTokenManager.generate_cart_token()
            )
            cart_token = cart.token

        # For digital products, no stock validation needed
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

        return True, cart_item, None, cart_token

    @staticmethod
    def update_cart_item(cart_item, quantity):
        """
        Update cart item quantity - no stock checking for digital products.
        """
        cart_item.quantity = quantity
        cart_item.save()
        return True, cart_item, None

    @staticmethod
    def remove_from_cart(cart_item):
        """
        Remove item from cart.
        """
        try:
            cart_item.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def clear_cart(cart_token):
        """
        Clear all items from cart.
        """
        try:
            cart = CartService.get_cart_from_token(cart_token)
            if cart:
                cart.clear()
                return True, cart_token
            return False, cart_token
        except Exception:
            return False, cart_token
