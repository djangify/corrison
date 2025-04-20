from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls', namespace='core')),
    path('products/', include('products.urls', namespace='products')),
    path('cart/', include('cart.urls', namespace='cart')),
    path('checkout/', include('checkout.urls', namespace='checkout')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('blog/', include('blog.urls', namespace='blog')),
    path('theme/', include('theme.urls', namespace='theme')),
    path('tinymce/', include('tinymce.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Enable Django Debug Toolbar in development
    try:
        import debug_toolbar
        urlpatterns.append(path('__debug__/', include(debug_toolbar.urls)))
    except ImportError:
        pass