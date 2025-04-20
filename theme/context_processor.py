# theme/context_processors.py

from django.conf import settings
from theme.services.theme_manager import ThemeService, SiteSettingsService, BannerService, FooterService


def theme_variables(request):
    """
    Context processor to add theme variables to all templates.
    
    Args:
        request: The HTTP request
        
    Returns:
        dict: Theme variables for templates
    """
    # Get the active theme
    theme = ThemeService.get_active_theme()
    
    # Get site settings
    site_settings = SiteSettingsService.get_settings()
    
    # Get social links
    social_links = SiteSettingsService.get_social_links()
    
    # Get active banners for the homepage
    banners = list(BannerService.get_active_banners())
    
    # Get footer links grouped by category
    footer_links = FooterService.get_footer_links()
    
    return {
        'theme': theme,
        'site_settings': site_settings,
        'social_links': social_links,
        'banners': banners,
        'footer_links': footer_links,
        'STRIPE_PUBLISHABLE_KEY': settings.STRIPE_PUBLISHABLE_KEY,
    }
