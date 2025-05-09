# cart/views.py
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from rest_framework.response import Response
from rest_framework import status
from products.models import Product, ProductVariant
from django.shortcuts import get_object_or_404
from cart.models import Cart, CartItem
from rest_framework.permissions import AllowAny


class CartViewSet(viewsets.GenericViewSet):
    serializer_class = CartSerializer
    
    # Modify the get_cart method in CartViewSet in cart/views.py
    def get_cart(self, request):
        """
        Get or create a cart for the current session or user.
        """
        user = request.user if request.user.is_authenticated else None
        session_key = request.session.session_key
        
        # Try to get an existing cart
        if user:
            # Check for user cart
            cart = Cart.objects.filter(user=user, is_active=True).first()
            
            # Check if there's a session cart to merge
            if session_key and not cart:
                session_cart = Cart.objects.filter(session_key=session_key, is_active=True).first()
                if session_cart:
                    # Transfer session cart to user
                    session_cart.user = user
                    session_cart.session_key = None
                    session_cart.save()
                    return session_cart
        else:
            # Create session if needed
            if not session_key:
                request.session.create()
                session_key = request.session.session_key
                # Ensure session is saved
                request.session.modified = True
                    
            # Check for session cart
            cart = Cart.objects.filter(session_key=session_key, is_active=True).first()
        
        # Create new cart if needed
        if not cart:
            cart = Cart.objects.create(
                user=user,
                session_key=None if user else session_key
            )
            # Make sure changes are saved
            request.session.modified = True
                
        return cart
        
    def list(self, request):
        """
        Get the current cart.
        """
        cart = self.get_cart(request)
        serializer = self.get_serializer(cart)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def clear(self, request):
        """
        Clear all items from the cart.
        """
        cart = self.get_cart(request)
        cart.items.all().delete()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)


class CartItemViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = CartItemSerializer
    
    def get_queryset(self):
        cart = self.get_cart(self.request)
        return CartItem.objects.filter(cart=cart)
    
    def get_cart(self, request):
        """
        Get or create the cart for the current user or session.
        """
        cart_viewset = CartViewSet()
        return cart_viewset.get_cart(request)
    
    def create(self, request, *args, **kwargs):
        """
        Add an item to the cart.
        """
        cart = self.get_cart(request)
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
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
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