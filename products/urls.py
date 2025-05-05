from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.catalog, name='catalog'),
    path('search/', views.search, name='search'),
    path('categories/', views.category_list, name='category_list'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('get-variant-price/', views.get_variant_price, name='get_variant_price'),
    path('<slug:slug>/', views.product_detail, name='product_detail'),
]
