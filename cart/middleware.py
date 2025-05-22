# cart/middleware.py
from .models import Cart

class CartMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
            request.session.save()  # Make sure the session is saved to DB
        
        # Add cart to request
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user, is_active=True).first()
            
            # Check if there's a session cart to merge
            session_key = request.session.session_key
            if session_key and not cart:
                session_cart = Cart.objects.filter(session_key=session_key, is_active=True).first()
                if session_cart:
                    # Transfer session cart to user
                    session_cart.user = request.user
                    session_cart.session_key = None
                    session_cart.save()
                    cart = session_cart
        else:
            # Ensure session key exists
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key
                request.session.save()  # Critical to save the session
                
            # Check for session cart
            cart = Cart.objects.filter(session_key=session_key, is_active=True).first()
        
        # Create new cart if needed
        if not cart:
            cart = Cart.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_key=None if request.user.is_authenticated else session_key
            )
            
        # Make sure cart is available to the request
        request.cart = cart
        
        # Ensure the session is saved
        request.session.modified = True
        
        # Process the request
        response = self.get_response(request)
        
        # Make sure the session cookie is being set
        if not request.user.is_authenticated:
            # Force save session again to ensure cookie is set
            request.session.save()
            
        return response