# cart/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from .utils import CartTokenManager
from products.models import Product, ProductVariant
from django.shortcuts import get_object_or_404
import logging

logger = logging.getLogger(__name__)


class CartViewSet(viewsets.GenericViewSet):
    serializer_class = CartSerializer
    permission_classes = [AllowAny]
    
    def get_cart_from_request(self, request):
        """
        Get or create a cart based on the request.
        Checks for cart token in Authorization header or creates new cart.
        """
        # Try to get token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        cart_token = None
        
        if auth_header.startswith('Bearer '):
            cart_token = auth_header.split(' ')[1]
        
        # Try to get cart by token
        cart = None
        if cart_token:
            cart_id = CartTokenManager.decode_cart_token(cart_token)
            if cart_id:
                cart = Cart.objects.filter(id=cart_id, is_active=True).first()
        
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
        
        return cart
        
    def list(self, request):
        """
        Get the current cart with token.
        """
        cart = self.get_cart_from_request(request)
        serializer = self.get_serializer(cart)
        
        # Add token to response
        data = serializer.data
        data['token'] = cart.token
        
        return Response(data)


class CartItemViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = CartItemSerializer
    
    def get_queryset(self):
        cart = self.get_cart_from_request(self.request)
        return CartItem.objects.filter(cart=cart)
    
    def get_cart_from_request(self, request):
        """
        Get cart from request using CartViewSet's method
        """
        cart_viewset = CartViewSet()
        return cart_viewset.get_cart_from_request(request)
    
    def create(self, request, *args, **kwargs):
        """
        Add an item to the cart.
        """
        cart = self.get_cart_from_request(request)
        
        product_id = request.data.get('product')
        variant_id = request.data.get('variant')
        quantity = int(request.data.get('quantity', 1))
        
        # Validate product and variant
        product = get_object_or_404(Product, pk=product_id)
        variant = None
        if variant_id:
            variant = get_object_or_404(ProductVariant, pk=variant_id, product=product)
        
        # Check stock
        if variant:
            if not variant.is_active or variant.stock_qty < quantity:
                return Response(
                    {'error': 'Not enough stock available'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            if not product.in_stock or product.stock_qty < quantity:
                return Response(
                    {'error': 'Not enough stock available'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
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
        
        serializer = self.get_serializer(cart_item)
        
        # Include cart token in response
        response_data = serializer.data
        response_data['cart_token'] = cart.token
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """
        Update cart item quantity.
        """
        cart_item = self.get_object()
        quantity = int(request.data.get('quantity', 1))
        
        # Check stock
        if cart_item.variant:
            if not cart_item.variant.is_active or cart_item.variant.stock_qty < quantity:
                return Response(
                    {'error': 'Not enough stock available'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            if not cart_item.product.in_stock or cart_item.product.stock_qty < quantity:
                return Response(
                    {'error': 'Not enough stock available'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        cart_item.quantity = quantity
        cart_item.save()
        
        serializer = self.get_serializer(cart_item)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """
        Remove item from cart.
        """
        cart_item = self.get_object()
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)