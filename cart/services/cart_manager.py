# cart/services/cart_manager.py
from cart.models import Cart, CartItem
from products.models import Product, ProductVariant


class CartService:
    """
    Service class for handling shopping cart operations.
    """
    
    @staticmethod
    def get_or_create_cart(request):
        """
        Get the current cart or create a new one.
        
        Args:
            request: The HTTP request
            
        Returns:
            Cart: The user's cart
        """
        return Cart.get_or_create_cart(request)
    
    @staticmethod
    def add_to_cart(request, product_id, quantity=1, variant_id=None):
        """
        Add a product to the cart.
        
        Args:
            request: The HTTP request
            product_id: ID of the product to add
            quantity: Quantity to add (default: 1)
            variant_id: ID of the variant to add (optional)
            
        Returns:
            tuple: (success, message, cart_item)
        """
        cart = CartService.get_or_create_cart(request)
        
        try:
            product = Product.objects.get(id=product_id, is_active=True)
            
            # Check if product is in stock
            if not product.in_stock or product.stock_qty < quantity:
                return False, "This product is out of stock or has insufficient quantity.", None
            
            variant = None
            if variant_id:
                try:
                    variant = ProductVariant.objects.get(id=variant_id, product=product, is_active=True)
                    
                    # Check if variant is in stock
                    if variant.stock_qty < quantity:
                        return False, "This variant is out of stock or has insufficient quantity.", None
                except ProductVariant.DoesNotExist:
                    return False, "The selected variant was not found.", None
            
            # Add the product to the cart
            cart_item = cart.add_item(product, quantity, variant)
            
            return True, f"{product.name} added to your cart.", cart_item
            
        except Product.DoesNotExist:
            return False, "The selected product was not found.", None
    
    @staticmethod
    def update_cart_item(request, item_id, quantity):
        """
        Update cart item quantity.
        
        Args:
            request: The HTTP request
            item_id: ID of the cart item to update
            quantity: New quantity
            
        Returns:
            tuple: (success, message)
        """
        cart = CartService.get_or_create_cart(request)
        
        # Validate quantity
        if quantity < 0:
            return False, "Quantity cannot be negative."
        
        if quantity == 0:
            # Remove the item if quantity is 0
            return CartService.remove_from_cart(request, item_id)
        
        # Try to update the item
        success = cart.update_item(item_id, quantity)
        
        if success:
            return True, "Cart updated successfully."
        return False, "The selected item was not found in your cart."
    
    @staticmethod
    def remove_from_cart(request, item_id):
        """
        Remove an item from the cart.
        
        Args:
            request: The HTTP request
            item_id: ID of the cart item to remove
            
        Returns:
            tuple: (success, message)
        """
        cart = CartService.get_or_create_cart(request)
        
        # Try to remove the item
        success = cart.remove_item(item_id)
        
        if success:
            return True, "Item removed from cart."
        return False, "The selected item was not found in your cart."
    
    @staticmethod
    def clear_cart(request):
        """
        Clear all items from the cart.
        
        Args:
            request: The HTTP request
            
        Returns:
            tuple: (success, message)
        """
        cart = CartService.get_or_create_cart(request)
        cart.clear()
        
        return True, "Your cart has been cleared."
    
    @staticmethod
    def get_cart_data(request):
        """
        Get cart data for display.
        
        Args:
            request: The HTTP request
            
        Returns:
            dict: Cart data including items, counts, and totals
        """
        cart = CartService.get_or_create_cart(request)
        
        # Get cart items with product details
        items = list(cart.items.select_related('product', 'variant').all())
        
        # Calculate subtotal
        subtotal = cart.subtotal
        
        # Calculate item count
        item_count = cart.item_count
        
        return {
            'cart': cart,
            'items': items,
            'subtotal': subtotal,
            'item_count': item_count
        }
    
    @staticmethod
    def migrate_cart_to_user(request):
        """
        Migrate an anonymous user's cart to a logged-in user.
        
        Args:
            request: The HTTP request
            
        Returns:
            Cart: The user's cart
        """
        if not request.user.is_authenticated:
            return None
        
        # Try to get session cart
        session_id = request.session.session_key
        if not session_id:
            return None
        
        session_cart = Cart.objects.filter(
            session_id=session_id, 
            user__isnull=True,
            is_active=True
        ).first()
        
        if not session_cart:
            return None
        
        # Try to get user cart
        user_cart = Cart.objects.filter(
            user=request.user,
            is_active=True
        ).first()
        
        if user_cart:
            # Merge session cart items into user cart
            for item in session_cart.items.all():
                # Check if the product already exists in the user cart
                existing_item = user_cart.items.filter(
                    product=item.product,
                    variant=item.variant
                ).first()
                
                if existing_item:
                    # Update quantity
                    existing_item.quantity += item.quantity
                    existing_item.save()
                else:
                    # Move item to user cart
                    item.cart = user_cart
                    item.save()
            
            # Delete the session cart
            session_cart.delete()
            return user_cart
        else:
            # Associate the session cart with the user
            session_cart.user = request.user
            session_cart.save()
            return session_cart
        