# cart/middleware.py
from .models import Cart
import logging

logger = logging.getLogger(__name__)

class CartMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip cart initialization for API endpoints that don't need it
        if request.path.startswith('/api/v1/products/') and request.method == 'GET':
            return self.get_response(request)
            
        # Skip for static files and media
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return self.get_response(request)
            
        try:
            # Ensure session exists
            if not request.session.session_key:
                request.session.create()
                request.session.save()
            
            # Add cart to request only for cart-related endpoints
            if request.path.startswith('/api/v1/cart/') or request.path.startswith('/api/v1/items/'):
                if request.user.is_authenticated:
                    cart = Cart.objects.filter(user=request.user, is_active=True).first()
                    
                    session_key = request.session.session_key
                    if session_key and not cart:
                        session_cart = Cart.objects.filter(session_key=session_key, is_active=True).first()
                        if session_cart:
                            session_cart.user = request.user
                            session_cart.session_key = None
                            session_cart.save()
                            cart = session_cart
                else:
                    session_key = request.session.session_key
                    if not session_key:
                        request.session.create()
                        session_key = request.session.session_key
                        request.session.save()
                        
                    cart = Cart.objects.filter(session_key=session_key, is_active=True).first()
                
                if not cart:
                    cart = Cart.objects.create(
                        user=request.user if request.user.is_authenticated else None,
                        session_key=None if request.user.is_authenticated else session_key
                    )
                    
                request.cart = cart
                request.session.modified = True
                
        except Exception as e:
            logger.error(f"CartMiddleware error: {e}")
            # Don't break the request if cart initialization fails
            pass
        
        response = self.get_response(request)
        
        return response