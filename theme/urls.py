from django.urls import path
from . import views

app_name = 'theme'

urlpatterns = [
    path('css/theme.css', views.theme_css, name='theme_css'),
    
    # Admin/staff views
    path('manager/', views.theme_manager, name='manager'),
    path('manager/activate/<uuid:theme_id>/', views.activate_theme, name='activate_theme'),
    path('manager/preview/<uuid:theme_id>/', views.preview_theme, name='preview_theme'),
    
    path('banners/', views.banner_manager, name='banner_manager'),
    path('banners/toggle/<uuid:banner_id>/', views.toggle_banner, name='toggle_banner'),
    path('banners/reorder/', views.reorder_banners, name='reorder_banners'),
    
    path('footer/', views.footer_manager, name='footer_manager'),
    path('footer/toggle/<uuid:link_id>/', views.toggle_footer_link, name='toggle_footer_link'),
    path('footer/reorder/', views.reorder_footer_links, name='reorder_footer_links'),
]
