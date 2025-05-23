# Update core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('contact/', views.submit_contact_message, name='submit_contact'),
    path('contact-settings/', views.get_contact_page_settings, name='contact_settings'),
]