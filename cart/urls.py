from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_view, name='cart'),
    path('add/', views.add_to_cart, name='add_to_cart'),
    path('update/', views.update_cart, name='update_cart'),
    path('remove/<uuid:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('clear/', views.clear_cart, name='clear_cart'),
    path('mini-cart/', views.mini_cart, name='mini_cart'),
]
