from django.urls import include, path
from rest_framework.routers import DefaultRouter
from blog.views import BlogPostViewSet
from linkhub.views import LinkHubViewSet
from pages.views import PageViewSet
from cart.views import CartViewSet, CartItemViewSet
from accounts.views import WishlistViewSet
from .views import (
    ProductViewSet,
    CategoryViewSet,
    AddressViewSet,
    OrderViewSet,
    PaymentViewSet,
    UserViewSet,
)

router = DefaultRouter()
router.register(r'wishlist', WishlistViewSet, basename='wishlist')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'addresses', AddressViewSet, basename='address')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'users', UserViewSet, basename='user')
router.register(r'blog/posts', BlogPostViewSet, basename='blog')
router.register(r'pages', PageViewSet, basename='page')
router.register(r'linkhubs', LinkHubViewSet, basename='linkhub')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'items', CartItemViewSet, basename='cart-item')


urlpatterns = [
    path('', include(router.urls)),
]