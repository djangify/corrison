from django.contrib.auth import get_user_model
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from products.models import Product
from checkout.models import Address, Order, Payment
from products.serializers import ProductSerializer
from .serializers import (
    
    AddressSerializer,
    OrderSerializer,
    PaymentSerializer,
    UserCreateUpdateSerializer,
)

User = get_user_model()

class ProductViewSet(viewsets.ModelViewSet):
    """
    Public catalog: list & retrieve for anonymous users;
    full CRUD for authenticated users.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'inventory']

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
