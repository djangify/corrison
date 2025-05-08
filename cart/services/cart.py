# cart/services/cart.py
from ..models import Cart, CartItem

class CartOperations:
    """
    Service class for cart operations beyond the basic manager.
    This could include specialized operations like merging carts,
    calculating discounts, applying coupons, etc.
    """
    
    @staticmethod
    def merge_carts(user_cart, session_cart):
        """
        Merge a session cart into a user cart.
        
        Args:
            user_cart: The destination cart (authenticated user)
            session_cart: The source cart (anonymous session)
            
        Returns:
            Cart: The merged cart
        """
        if not user_cart or not session_cart:
            return user_cart or session_cart
        
        # Copy items from session cart to user cart
        for item in session_cart.items.all():
            try:
                # Try to find matching item in user cart
                user_item = CartItem.objects.get(
                    cart=user_cart,
                    product=item.product,
                    variant=item.variant
                )
                # Update quantity
                user_item.quantity += item.quantity
                user_item.save()
            except CartItem.DoesNotExist:
                # Create new item in user cart
                item.pk = None  # Reset primary key to create a new record
                item.cart = user_cart
                item.save()
        
        # Delete the session cart
        session_cart.delete()
        
        return user_cart