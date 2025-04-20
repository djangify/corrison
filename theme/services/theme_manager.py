# theme/services/theme_manager.py
from django.conf import settings
from theme.models import Theme, SiteSettings, Banner, FooterLink


class ThemeService:
    """
    Service class for managing theme-related functionality.
    """
    
    @staticmethod
    def get_active_theme():
        """
        Get the active theme or create a default one if none exists.
        
        Returns:
            Theme: The active theme
        """
        return Theme.get_active_theme()
    
    @staticmethod
    def get_theme_by_name(name):
        """
        Get a theme by its name.
        
        Args:
            name: The theme name
            
        Returns:
            Theme: The theme or None if not found
        """
        try:
            return Theme.objects.get(name=name)
        except Theme.DoesNotExist:
            return None
    
    @staticmethod
    def set_active_theme(theme_name):
        """
        Set a theme as active by its name.
        
        Args:
            theme_name: The name of the theme to activate
            
        Returns:
            tuple: (success, message, theme)
        """
        try:
            theme = Theme.objects.get(name=theme_name)
            
            # Set as active (this will also deactivate other themes)
            theme.is_active = True
            theme.save()
            
            return True, f"Theme '{theme_name}' has been activated.", theme
        except Theme.DoesNotExist:
            return False, f"Theme '{theme_name}' not found.", None
    
    @staticmethod
    def create_or_update_theme(name, **theme_data):
        """
        Create a new theme or update an existing one.
        
        Args:
            name: The theme name
            **theme_data: Theme data
            
        Returns:
            tuple: (theme, created)
        """
        theme, created = Theme.objects.update_or_create(
            name=name,
            defaults=theme_data
        )
        
        return theme, created
    
    @staticmethod
    def get_all_themes():
        """
        Get all available themes.
        
        Returns:
            QuerySet: All themes
        """
        return Theme.objects.all()
    
    @staticmethod
    def delete_theme(theme_name):
        """
        Delete a theme by its name.
        
        Args:
            theme_name: The name of the theme to delete
            
        Returns:
            tuple: (success, message)
        """
        try:
            theme = Theme.objects.get(name=theme_name)
            
            # Don't allow deleting the active theme
            if theme.is_active:
                return False, "Cannot delete the active theme."
            
            theme.delete()
            return True, f"Theme '{theme_name}' has been deleted."
        except Theme.DoesNotExist:
            return False, f"Theme '{theme_name}' not found."
    
    @staticmethod
    def get_theme_css_variables(theme=None):
        """
        Get CSS variables for the theme.
        
        Args:
            theme: The theme to get variables for (uses active theme if None)
            
        Returns:
            str: CSS variables as a string
        """
        if theme is None:
            theme = ThemeService.get_active_theme()
        
        # Build CSS variables string
        css_vars = [
            ":root {",
            f"  --primary: {theme.primary_color};",
            f"  --primary-dark: {theme.primary_dark_color};",
            f"  --primary-light: {theme.primary_light_color};",
            
            f"  --secondary: {theme.secondary_color};",
            f"  --secondary-dark: {theme.secondary_dark_color};",
            f"  --secondary-light: {theme.secondary_light_color};",
            
            f"  --accent: {theme.accent_color};",
            
            f"  --success: {theme.success_color};",
            f"  --info: {theme.info_color};",
            f"  --warning: {theme.warning_color};",
            f"  --danger: {theme.danger_color};",
            
            f"  --background: {theme.background_color};",
            f"  --text: {theme.text_color};",
            
            f"  --font-primary: {theme.font_primary};",
            f"  --font-headings: {theme.font_headings};",
            
            f"  --spacing-unit: {theme.spacing_unit};",
            f"  --border-radius: {theme.border_radius};",
            
            f"  --footer-background: {theme.footer_background};",
            f"  --footer-text: {theme.footer_text_color};",
            
            f"  --button-border-radius: {theme.button_border_radius};",
            
            f"  --header-background: {theme.header_background};",
            f"  --header-text: {theme.header_text_color};",
            
            f"  --nav-background: {theme.nav_background};",
            f"  --nav-text: {theme.nav_text_color};",
            f"  --nav-active: {theme.nav_active_color};",
            
            f"  --product-card-background: {theme.product_card_background};",
            f"  --product-card-text: {theme.product_card_text_color};",
            f"  --product-card-border: {theme.product_card_border};",
            "}"
        ]
        
        return "\n".join(css_vars)


class SiteSettingsService:
    """
    Service class for managing site settings.
    """
    
    @staticmethod
    def get_settings():
        """
        Get the site settings or create default settings if none exist.
        
        Returns:
            SiteSettings: The site settings
        """
        return SiteSettings.get_settings()
    
    @staticmethod
    def update_settings(**settings_data):
        """
        Update site settings.
        
        Args:
            **settings_data: Settings data
            
        Returns:
            SiteSettings: The updated settings
        """
        settings = SiteSettingsService.get_settings()
        
        # Update fields
        for key, value in settings_data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        settings.save()
        return settings
    
    @staticmethod
    def get_social_links():
        """
        Get social media links from site settings.
        
        Returns:
            dict: Social media links
        """
        settings = SiteSettingsService.get_settings()
        
        return {
            'facebook': settings.facebook_url,
            'twitter': settings.twitter_url,
            'instagram': settings.instagram_url,
            'youtube': settings.youtube_url,
        }
    

class BannerService:
    """
    Service class for managing banners.
    """
    
    @staticmethod
    def get_active_banners():
        """
        Get all active banners ordered by their position.
        
        Returns:
            QuerySet: Active banners
        """
        return Banner.objects.filter(is_active=True).order_by('order')
    
    @staticmethod
    def create_banner(title, image, **banner_data):
        """
        Create a new banner.
        
        Args:
            title: Banner title
            image: Banner image
            **banner_data: Additional banner data
            
        Returns:
            Banner: The created banner
        """
        return Banner.objects.create(
            title=title,
            image=image,
            **banner_data
        )
    
    @staticmethod
    def update_banner(banner_id, **banner_data):
        """
        Update a banner.
        
        Args:
            banner_id: ID of the banner to update
            **banner_data: Updated banner data
            
        Returns:
            tuple: (success, banner)
        """
        try:
            banner = Banner.objects.get(id=banner_id)
            
            # Update fields
            for key, value in banner_data.items():
                if hasattr(banner, key):
                    setattr(banner, key, value)
            
            banner.save()
            return True, banner
        except Banner.DoesNotExist:
            return False, None
    
    @staticmethod
    def delete_banner(banner_id):
        """
        Delete a banner.
        
        Args:
            banner_id: ID of the banner to delete
            
        Returns:
            bool: Success status
        """
        try:
            banner = Banner.objects.get(id=banner_id)
            banner.delete()
            return True
        except Banner.DoesNotExist:
            return False


class FooterService:
    """
    Service class for managing footer links.
    """
    
    @staticmethod
    def get_footer_links():
        """
        Get all active footer links grouped by category.
        
        Returns:
            dict: Footer links grouped by category
        """
        links = FooterLink.objects.filter(is_active=True).order_by('category', 'order')
        
        # Group by category
        grouped_links = {}
        for link in links:
            if link.category not in grouped_links:
                grouped_links[link.category] = []
            
            grouped_links[link.category].append(link)
        
        return grouped_links
    
    @staticmethod
    def create_footer_link(title, url, category, **link_data):
        """
        Create a new footer link.
        
        Args:
            title: Link title
            url: Link URL
            category: Link category
            **link_data: Additional link data
            
        Returns:
            FooterLink: The created link
        """
        return FooterLink.objects.create(
            title=title,
            url=url,
            category=category,
            **link_data
        )
    
    @staticmethod
    def update_footer_link(link_id, **link_data):
        """
        Update a footer link.
        
        Args:
            link_id: ID of the link to update
            **link_data: Updated link data
            
        Returns:
            tuple: (success, link)
        """
        try:
            link = FooterLink.objects.get(id=link_id)
            
            # Update fields
            for key, value in link_data.items():
                if hasattr(link, key):
                    setattr(link, key, value)
            
            link.save()
            return True, link
        except FooterLink.DoesNotExist:
            return False, None
    
    @staticmethod
    def delete_footer_link(link_id):
        """
        Delete a footer link.
        
        Args:
            link_id: ID of the link to delete
            
        Returns:
            bool: Success status
        """
        try:
            link = FooterLink.objects.get(id=link_id)
            link.delete()
            return True
        except FooterLink.DoesNotExist:
            return False
