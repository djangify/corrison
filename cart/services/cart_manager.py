# cart/services/cart_manager.py
from ..models import Cart, CartItem

class CartService:
    """
    Service class for managing cart operations.
    """
    @staticmethod
    def get_cart_data(request):
        """
        Get cart data for the current user or session.
        
        Args:
            request: The HTTP request
            
        Returns:
            dict: Cart data including cart object, items, subtotal, and item count
        """
        user = request.user if request.user.is_authenticated else None
        session_key = request.session.session_key
        
        # Get or create cart
        if user:
            cart = Cart.objects.filter(user=user, is_active=True).first()
        else:
            # Create session if needed
            if not session_key:
                request.session.create()
                session_key = request.session.session_key
                
            cart = Cart.objects.filter(session_key=session_key, is_active=True).first()
        
        # If no cart exists, create one
        if not cart:
            cart = Cart.objects.create(
                user=user,
                session_key=None if user else session_key
            )
        
        # Get cart items
        items = cart.items.select_related('product', 'variant').all()
        
        # Calculate totals
        subtotal = cart.subtotal
        item_count = cart.total_items
        
        return {
            'cart': cart,
            'items': items,
            'subtotal': subtotal,
            'item_count': item_count
        }
    
    @staticmethod
    def add_to_cart(request, product, variant=None, quantity=1):
        """
        Add a product to the cart.
        
        Args:
            request: The HTTP request
            product: The product to add
            variant: The product variant (optional)
            quantity: The quantity to add
            
        Returns:
            tuple: (success, cart_item, error_message)
        """
        # Get or create cart
        user = request.user if request.user.is_authenticated else None
        session_key = request.session.session_key
        
        if user:
            cart = Cart.objects.filter(user=user, is_active=True).first()
        else:
            # Create session if needed
            if not session_key:
                request.session.create()
                session_key = request.session.session_key
                
            cart = Cart.objects.filter(session_key=session_key, is_active=True).first()
        
        # If no cart exists, create one
        if not cart:
            cart = Cart.objects.create(
                user=user,
                session_key=None if user else session_key
            )
        
        # Check stock
        if variant:
            if not variant.is_active or variant.stock_qty < quantity:
                return False, None, "Not enough stock available"
        else:
            if not product.in_stock or product.stock_qty < quantity:
                return False, None, "Not enough stock available"
        
        # Check if item already exists in cart
        try:
            cart_item = CartItem.objects.get(cart=cart, product=product, variant=variant)
            # Update quantity
            cart_item.quantity += quantity
            cart_item.save()
        except CartItem.DoesNotExist:
            # Create new item
            cart_item = CartItem.objects.create(
                cart=cart,
                product=product,
                variant=variant,
                quantity=quantity
            )
        
        return True, cart_item, None
    
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
        # Check stock
        if cart_item.variant:
            if not cart_item.variant.is_active or cart_item.variant.stock_qty < quantity:
                return False, None, "Not enough stock available"
        else:
            if not cart_item.product.in_stock or cart_item.product.stock_qty < quantity:
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
    def clear_cart(cart):
        """
        Clear all items from the cart.
        
        Args:
            cart: The cart to clear
            
        Returns:
            bool: Success or failure
        """
        try:
            cart.items.all().delete()
            return True
        except Exception:
            return False