from django.urls import path
from . import views

app_name = 'checkout'

urlpatterns = [
    path('', views.checkout, name='checkout'),
    path('process/', views.process_checkout, name='process_checkout'),
    path('payment/', views.payment, name='payment'),
    path('confirmation/<str:order_number>/', views.confirmation, name='confirmation'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<str:order_number>/', views.order_detail, name='order_detail'),
    path('orders/<str:order_number>/cancel/', views.cancel_order, name='cancel_order'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
]
