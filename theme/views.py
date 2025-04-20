# theme/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from .models import Theme, SiteSettings, Banner, FooterLink
from .services.theme_manager import ThemeService, SiteSettingsService, BannerService, FooterService


def theme_css(request):
    """
    View to serve theme CSS variables.
    """
    # Get the active theme
    theme = ThemeService.get_active_theme()
    
    # Generate CSS variables
    css_content = ThemeService.get_theme_css_variables(theme)
    
    # Add custom CSS if provided
    if theme.custom_css:
        css_content += f"\n\n/* Custom CSS */\n{theme.custom_css}"
    
    # Return as a CSS file
    response = HttpResponse(css_content, content_type='text/css')
    return response


@staff_member_required
def theme_manager(request):
    """
    Theme manager view for admins.
    """
    # Get all themes
    themes = ThemeService.get_all_themes()
    
    # Get active theme
    active_theme = ThemeService.get_active_theme()
    
    context = {
        'themes': themes,
        'active_theme': active_theme
    }
    
    return render(request, 'theme/manager.html', context)


@staff_member_required
def activate_theme(request, theme_id):
    """
    Activate a theme.
    """
    theme = Theme.objects.get(id=theme_id)
    
    # Set as active
    theme.is_active = True
    theme.save()
    
    messages.success(request, f'Theme "{theme.name}" has been activated.')
    
    return redirect('theme:manager')


@staff_member_required
def preview_theme(request, theme_id):
    """
    Preview a theme without activating it.
    """
    theme = Theme.objects.get(id=theme_id)
    
    # Generate CSS variables
    css_content = ThemeService.get_theme_css_variables(theme)
    
    # Add custom CSS if provided
    if theme.custom_css:
        css_content += f"\n\n/* Custom CSS */\n{theme.custom_css}"
    
    context = {
        'theme': theme,
        'css_content': css_content,
        'preview': True
    }
    
    return render(request, 'theme/preview.html', context)


@staff_member_required
def banner_manager(request):
    """
    Banner manager view for admins.
    """
    # Get all banners
    banners = Banner.objects.all().order_by('order')
    
    context = {
        'banners': banners
    }
    
    return render(request, 'theme/banner_manager.html', context)


@staff_member_required
def toggle_banner(request, banner_id):
    """
    Toggle banner active status.
    """
    banner = Banner.objects.get(id=banner_id)
    
    # Toggle active status
    banner.is_active = not banner.is_active
    banner.save()
    
    status = 'activated' if banner.is_active else 'deactivated'
    messages.success(request, f'Banner "{banner.title}" has been {status}.')
    
    return redirect('theme:banner_manager')


@staff_member_required
def footer_manager(request):
    """
    Footer link manager view for admins.
    """
    # Get all footer links
    footer_links = FooterLink.objects.all().order_by('category', 'order')
    
    context = {
        'footer_links': footer_links,
        'categories': dict(FooterLink.CATEGORY_CHOICES)
    }
    
    return render(request, 'theme/footer_manager.html', context)


@staff_member_required
def toggle_footer_link(request, link_id):
    """
    Toggle footer link active status.
    """
    link = FooterLink.objects.get(id=link_id)
    
    # Toggle active status
    link.is_active = not link.is_active
    link.save()
    
    status = 'activated' if link.is_active else 'deactivated'
    messages.success(request, f'Footer link "{link.title}" has been {status}.')
    
    return redirect('theme:footer_manager')


@staff_member_required
def reorder_banners(request):
    """
    AJAX view to reorder banners.
    """
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            # Get the new order
            banner_order = request.POST.getlist('banner_order[]')
            
            # Update banner positions
            for i, banner_id in enumerate(banner_order):
                banner = Banner.objects.get(id=banner_id)
                banner.order = i
                banner.save()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


@staff_member_required
def reorder_footer_links(request):
    """
    AJAX view to reorder footer links.
    """
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            # Get the new order
            link_order = request.POST.getlist('link_order[]')
            
            # Update link positions
            for i, link_id in enumerate(link_order):
                link = FooterLink.objects.get(id=link_id)
                link.order = i
                link.save()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})
