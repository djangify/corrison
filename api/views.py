# api/views.py
from django.contrib.auth import get_user_model
from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.http import HttpResponse
from PIL import Image
from io import BytesIO
import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from products.models import Product, Category
from rest_framework.viewsets import ReadOnlyModelViewSet
from checkout.models import Address, Order, Payment
from products.serializers import ProductSerializer
from .serializers import (
    
    AddressSerializer,
    OrderSerializer,
    PaymentSerializer,
    UserCreateUpdateSerializer,
    CategorySerializer,
)

User = get_user_model()

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for products.
    Allows GET requests to list and retrieve products.
    Uses slug for lookups.
    """
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    lookup_field = 'slug'
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['name', 'price', 'created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        # Add prefetching to reduce DB queries
        return queryset.select_related('category').prefetch_related('images', 'variants')

class CategoryViewSet(ReadOnlyModelViewSet):
    """
    A viewset for viewing categories.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class AddressViewSet(viewsets.ModelViewSet):
    """
    Addresses: authenticated users only.
    """
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

class OrderViewSet(viewsets.ModelViewSet):
    """
    Orders: authenticated users only.
    """
    # prefetch to pull in the items efficiently
    queryset = Order.objects.prefetch_related('items').all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

class PaymentViewSet(viewsets.ModelViewSet):
    """
    Payments: authenticated users only.
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(order__user=self.request.user)

class UserViewSet(viewsets.ModelViewSet):
    """
    - POST (create): open to anyone (registration)
    - GET/PUT/PATCH (update): only for the authenticated user
    """
    queryset = User.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        # for signup (no instance yet), and for profile updates, use our create/update serializer
        return UserCreateUpdateSerializer

    def get_permissions(self):
        if self.action == 'create':
            # anyone can register
            return [AllowAny()]
        # all other actions require auth
        return [IsAuthenticated()]
    
    def get_queryset(self):
        # even for list/retrieve, lock down to yourself
        return User.objects.filter(id=self.request.user.id)

# In api/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['POST'])
def add_to_cart(request):
    # Handle adding items to cart
    pass

@api_view(['PUT'])
def update_cart_item(request):
    # Handle updating cart item quantity
    pass

@api_view(['DELETE'])
def remove_cart_item(request):
    # Handle removing items from cart
    pass

@api_view(['POST'])
def create_payment_intent(request):
    # Handle Stripe payment intent creation
    pass

@api_view(['POST'])
def create_order(request):
    # Handle order creation
    pass

@api_view(['GET'])
def placeholder_image(request, width, height):
    # Generate placeholder images
    pass    