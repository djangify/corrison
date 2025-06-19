# cart/services/cart_manager.py
from ..models import Cart


class CartService:
    """
    Simple session-based cart service for digital products.
    """

    @staticmethod
    def get_cart_data(request, cart_token=None):
        """
        Get cart data using Django sessions.
        """
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()

        session_key = request.session.session_key

        # Get or create cart for this session
        cart, created = Cart.objects.get_or_create(
            session_key=session_key,
            is_active=True,
            defaults={"user": request.user if request.user.is_authenticated else None},
        )

        # If user is authenticated and cart has no user, assign it
        if request.user.is_authenticated and not cart.user:
            cart.user = request.user
            cart.save(update_fields=["user"])

        # Get cart items
        items = cart.items.select_related("product", "variant").all()

        # Calculate subtotal safely
        subtotal = float(cart.subtotal) if cart.subtotal else 0.0

        return {
            "cart": cart,
            "items": items,
            "subtotal": subtotal,
            "item_count": cart.total_items,
            "cart_token": session_key,  # Use session_key as token for compatibility
            # Digital-only flags
            "has_digital_items": True,
            "has_physical_items": False,
            "is_digital_only": True,
            "requires_shipping": False,
        }
