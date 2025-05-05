# core/views.py
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import ContactMessage


def index(request):
    """
    Home/Index page view.
    """
    context = {
        'page_title': 'Corrison - Home',
        'breadcrumbs': [
            {'title': 'Home'}
        ]
    }

    return render(request, 'index.html', context)
