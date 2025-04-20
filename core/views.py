# core/views.py
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

from products.services.catalog import CatalogService
from theme.models import Banner
from blog.models import Post
from django.utils import timezone
from .models import ContactMessage


def index(request):
    """
    Home/Index page view.
    """
    # Get featured products
    featured_products = CatalogService.get_featured_products(limit=8)
    
    # Get new arrivals
    new_arrivals = CatalogService.get_new_arrivals(limit=4)
    
    # Get on sale products
    on_sale_products = CatalogService.get_on_sale_products(limit=4)
    
    # Get active banners
    banners = Banner.objects.filter(is_active=True).order_by('order')
    
    # Get featured blog posts
    blog_posts = Post.objects.filter(
        status="published",
        featured=True,
        publish_date__lte=timezone.now()
    ).order_by('-publish_date')[:3]
    
    context = {
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'on_sale_products': on_sale_products,
        'banners': banners,
        'blog_posts': blog_posts,
    }
    
    return render(request, 'index.html', context)


def about(request):
    """
    About page view.
    """
    context = {
        'page_title': 'About Us',
        'breadcrumbs': [
            {'title': 'Home', 'url': '/'},
            {'title': 'About Us'}
        ]
    }
    return render(request, 'core/about.html', context)


def contact(request):
    """
    Contact page view with form processing.
    """
    context = {
        'page_title': 'Contact Us',
        'breadcrumbs': [
            {'title': 'Home', 'url': '/'},
            {'title': 'Contact Us'}
        ]
    }
    
    if request.method == 'POST':
        # Process the contact form
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message_content = request.POST.get('message')
        
        # Store the message in the database
        contact_message = ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message_content
        )
        
        # Optionally send notification email to admin
        try:
            admin_email = settings.DEFAULT_FROM_EMAIL
            email_subject = f"New Contact Message: {subject}"
            email_message = f"""
You have received a new contact message from {name} ({email}):

Subject: {subject}

Message:
{message_content}

---
This message was sent from the contact form on your website.
            """
            
            send_mail(
                email_subject,
                email_message,
                settings.DEFAULT_FROM_EMAIL,
                [admin_email],
                fail_silently=False,
            )
        except Exception as e:
            # Log the error but don't show it to the user
            print(f"Error sending email notification: {str(e)}")
        
        # Show success message to the user
        messages.success(request, "Thank you for your message! We'll get back to you as soon as possible.")
        
        # Add success status to context
        context['success'] = True
        context['message'] = "Thank you for your message! We'll get back to you as soon as possible."
    
    return render(request, 'core/contact.html', context)


def faq(request):
    """
    FAQ page view.
    """
    return render(request, 'core/faq.html')


def privacy_policy(request):
    """
    Privacy policy page view.
    """
    return render(request, 'core/privacy_policy.html')


def terms_conditions(request):
    """
    Terms and conditions page view.
    """
    return render(request, 'core/terms_conditions.html')


class CustomErrorView(TemplateView):
    """
    Custom error views.
    """
    
    def get_template_names(self):
        status_code = self.kwargs.get('status_code', 404)
        return [f'core/errors/{status_code}.html', 'core/errors/error.html']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        status_code = self.kwargs.get('status_code', 404)
        context['status_code'] = status_code
        
        if status_code == 404:
            context['error_title'] = 'Page Not Found'
            context['error_message'] = 'The page you are looking for does not exist.'
        elif status_code == 403:
            context['error_title'] = 'Forbidden'
            context['error_message'] = 'You do not have permission to access this page.'
        elif status_code == 500:
            context['error_title'] = 'Server Error'
            context['error_message'] = 'An error occurred on our server. Please try again later.'
        else:
            context['error_title'] = 'Error'
            context['error_message'] = 'An error occurred. Please try again later.'
        
        return context


def handler404(request, exception):
    """
    404 error handler.
    """
    return CustomErrorView.as_view()(request, status_code=404)


def handler500(request):
    """
    500 error handler.
    """
    return CustomErrorView.as_view()(request, status_code=500)
