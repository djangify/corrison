# cart/middleware.py
from .models import Cart

# cart/middleware.py
class CartMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
        
        # Add cart to request
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user, is_active=True).first()
        else:
            session_key = request.session.session_key
            cart = Cart.objects.filter(session_key=session_key, is_active=True).first()
        
        if not cart:
            cart = Cart.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_key=None if request.user.is_authenticated else request.session.session_key
            )
        
        # Ensure session is saved
        request.session.save()
        
        request.cart = cart
        
        response = self.get_response(request)
        
        return response