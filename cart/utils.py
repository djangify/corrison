# cart/utils.py
import uuid


class CartTokenManager:
    """
    Simple UUID-based cart token manager.
    No more JWT complexity - just simple UUIDs.
    """

    @staticmethod
    def generate_cart_token():
        """
        Generate a simple UUID token for cart identification.
        """
        return str(uuid.uuid4())

    @staticmethod
    def is_valid_token(token):
        """
        Basic token validation - just check if it's a valid UUID format.
        """
        try:
            uuid.UUID(token)
            return True
        except (ValueError, TypeError):
            return False
