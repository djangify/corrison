# cart/services/cart_manager.py
from ..models import Cart, CartItem
from ..utils import CartTokenManager


class CartService:
    """
    Service class for managing cart operations using JWT tokens.
    """

    @staticmethod
    def get_cart_from_token(cart_token):
        """
        Get cart by JWT token.

        Args:
            cart_token: JWT token string

        Returns:
            Cart: Cart object or None if not found
        """
        if not cart_token:
            return None

        cart_id = CartTokenManager.decode_cart_token(cart_token)
        if cart_id:
            return Cart.objects.filter(id=cart_id, is_active=True).first()
        return None

    @staticmethod
    def get_cart_data(request, cart_token=None):
        """
        Get cart data using JWT token or create new cart.

        Args:
            request: The HTTP request
            cart_token: Optional JWT cart token

        Returns:
            dict: Cart data including cart object, items, subtotal, and item count
        """
        cart = None

        # Try to get cart token from multiple sources
        if not cart_token:
            # Try Authorization header
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                cart_token = auth_header.split(" ")[1]

        # Get cart by token
        if cart_token:
            cart = CartService.get_cart_from_token(cart_token)

        # If no cart found and user is authenticated, try to get user's cart
        if not cart and request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user, is_active=True).first()

        # Create new cart if needed
        if not cart:
            cart = Cart.objects.create(
                user=request.user if request.user.is_authenticated else None
            )
            # Generate token for new cart
            new_token = CartTokenManager.generate_cart_token(cart.id)
            cart.token = new_token
            cart.save()

        # Ensure cart has a token
        if not cart.token:
            cart.token = CartTokenManager.generate_cart_token(cart.id)
            cart.save()

        # Get cart items
        items = cart.items.select_related("product", "variant").all()

        # Calculate totals using model properties
        subtotal = cart.subtotal
        item_count = cart.total_items

        return {
            "cart": cart,
            "items": items,
            "subtotal": subtotal,
            "item_count": item_count,
            "cart_token": cart.token,
            "has_digital_items": cart.has_digital_items,
            "has_physical_items": cart.has_physical_items,
            "is_digital_only": cart.is_digital_only,
            "requires_shipping": cart.requires_shipping,
        }

    @staticmethod
    def add_to_cart(cart_token, product, variant=None, quantity=1, user=None):
        """
        Add a product to the cart using JWT token.

        Args:
            cart_token: JWT cart token
            product: The product to add
            variant: The product variant (optional)
            quantity: The quantity to add
            user: The user (optional, for creating new cart if token invalid)

        Returns:
            tuple: (success, cart_item, error_message, cart_token)
        """
        # Get or create cart
        cart = None
        if cart_token:
            cart = CartService.get_cart_from_token(cart_token)

        # If no cart found, create new one
        if not cart:
            cart = Cart.objects.create(user=user)
            new_token = CartTokenManager.generate_cart_token(cart.id)
            cart.token = new_token
            cart.save()
            cart_token = new_token

        # Check stock for physical products
        if variant:
            if not variant.is_active:
                return False, None, "Product variant is not available", cart_token
            if product.product_type == "physical" and variant.stock_qty < quantity:
                return False, None, "Not enough stock available", cart_token
        else:
            if product.product_type == "physical":
                if not product.in_stock or product.stock_qty < quantity:
                    return False, None, "Not enough stock available", cart_token

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
        Update cart item quantity.

        Args:
            cart_item: The cart item to update
            quantity: The new quantity

        Returns:
            tuple: (success, cart_item, error_message)
        """
        # Check stock for physical products
        if cart_item.variant:
            if not cart_item.variant.is_active:
                return False, None, "Product variant is not available"
            if (
                cart_item.product.product_type == "physical"
                and cart_item.variant.stock_qty < quantity
            ):
                return False, None, "Not enough stock available"
        else:
            if cart_item.product.product_type == "physical":
                if (
                    not cart_item.product.in_stock
                    or cart_item.product.stock_qty < quantity
                ):
                    return False, None, "Not enough stock available"

        cart_item.quantity = quantity
        cart_item.save()

        return True, cart_item, None

    @staticmethod
    def remove_from_cart(cart_item):
        """
        Remove an item from the cart.

        Args:
            cart_item: The cart item to remove

        Returns:
            bool: Success or failure
        """
        try:
            cart_item.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def clear_cart(cart_token):
        """
        Clear all items from the cart using JWT token.

        Args:
            cart_token: JWT cart token

        Returns:
            tuple: (success, cart_token)
        """
        try:
            cart = CartService.get_cart_from_token(cart_token)
            if cart:
                cart.clear()  # Uses the model's clear method
                return True, cart_token
            return False, cart_token
        except Exception:
            return False, cart_token

    @staticmethod
    def merge_carts_on_login(user, anonymous_cart_token):
        """
        Merge anonymous cart with user's cart when user logs in.

        Args:
            user: The authenticated user
            anonymous_cart_token: JWT token of anonymous cart

        Returns:
            str: JWT token of the merged cart
        """
        # Get user's existing cart
        user_cart = Cart.objects.filter(user=user, is_active=True).first()

        # Get anonymous cart
        anonymous_cart = (
            CartService.get_cart_from_token(anonymous_cart_token)
            if anonymous_cart_token
            else None
        )

        if not anonymous_cart:
            # No anonymous cart to merge, just return user's cart token
            if not user_cart:
                user_cart = Cart.objects.create(user=user)
                user_cart.token = CartTokenManager.generate_cart_token(user_cart.id)
                user_cart.save()
            elif not user_cart.token:
                user_cart.token = CartTokenManager.generate_cart_token(user_cart.id)
                user_cart.save()
            return user_cart.token

        if not user_cart:
            # No user cart exists, convert anonymous cart to user cart
            anonymous_cart.user = user
            anonymous_cart.save()
            return anonymous_cart.token

        # Merge anonymous cart into user cart
        from .cart import CartOperations

        merged_cart = CartOperations.merge_carts(user_cart, anonymous_cart)

        # Ensure merged cart has a token
        if not merged_cart.token:
            merged_cart.token = CartTokenManager.generate_cart_token(merged_cart.id)
            merged_cart.save()

        return merged_cart.token
