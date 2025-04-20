from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('orders/', views.order_history, name='order_history'),
    path('orders/<str:order_number>/', views.order_detail, name='order_detail'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/add/<uuid:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<uuid:item_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
]
