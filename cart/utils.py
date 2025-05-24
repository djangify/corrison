# cart/utils.py
import jwt
import uuid
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone

class CartTokenManager:
    """
    Manages JWT tokens for cart operations
    """
    SECRET_KEY = settings.SECRET_KEY
    ALGORITHM = 'HS256'
    TOKEN_EXPIRY_DAYS = 30
    
    @classmethod
    def generate_cart_token(cls, cart_id):
        """
        Generate a JWT token for a cart
        """
        payload = {
            'cart_id': str(cart_id),
            'exp': datetime.utcnow() + timedelta(days=cls.TOKEN_EXPIRY_DAYS),
            'iat': datetime.utcnow(),
            'type': 'cart_token'
        }
        
        token = jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        return token
    
    @classmethod
    def decode_cart_token(cls, token):
        """
        Decode and validate a cart token
        Returns cart_id if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            
            # Verify token type
            if payload.get('type') != 'cart_token':
                return None
                
            return payload.get('cart_id')
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @classmethod
    def refresh_cart_token(cls, old_token):
        """
        Refresh an existing cart token
        """
        cart_id = cls.decode_cart_token(old_token)
        if cart_id:
            return cls.generate_cart_token(cart_id)
        return None