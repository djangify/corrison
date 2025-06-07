## urls for main corrison project.
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.views.static import serve


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("api.urls")),
    path("auth/", include("accounts.urls")),  # ← ADD THIS LINE
    path("", TemplateView.as_view(template_name="index.html"), name="home"),
    path("tinymce/", include("tinymce.urls")),
    path(
        "media/<path:path>",
        serve,
        {
            "document_root": settings.MEDIA_ROOT,
        },
    ),
]
