# core/views.py
from django.shortcuts import render
from django.views.generic import TemplateView
from products.services.catalog import CatalogService
from theme.models import Banner
from blog.models import Post
from django.utils import timezone


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
    return render(request, 'core/about.html')


def contact(request):
    """
    Contact page view.
    """
    if request.method == 'POST':
        # Process the contact form (send email, save to database, etc.)
        # This is just a placeholder - implement according to your needs
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Here you would typically send an email or save to database
        # For example, you could use Django's send_mail function
        
        context = {
            'success': True,
            'message': 'Your message has been sent. We will get back to you soon.'
        }
        
        return render(request, 'core/contact.html', context)
    
    return render(request, 'core/contact.html')


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
