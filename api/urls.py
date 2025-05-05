from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet,
    AddressViewSet,
    OrderViewSet,
    PaymentViewSet,
    UserViewSet,
)

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'addresses', AddressViewSet, basename='address')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]