# cart/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'cart'

router = DefaultRouter()  # Define the router
router.register(r'', views.CartViewSet, basename='cart')
router.register(r'items', views.CartItemViewSet, basename='cart-item')

urlpatterns = [
    path('', include(router.urls)),
]