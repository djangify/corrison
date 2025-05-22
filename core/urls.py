# Update core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('contact/', views.submit_contact_message, name='submit_contact'),
]