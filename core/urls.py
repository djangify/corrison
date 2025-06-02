from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    # Site Settings API (NEW)
    path("site-settings/", views.site_settings, name="site-settings"),
    # Contact Form API (EXISTING + NEW)
    path("contact/", views.submit_contact_message, name="submit-contact"),
    path(
        "contact-page-settings/",
        views.contact_page_settings,
        name="contact-page-settings",
    ),
    path(
        "get-contact-page-settings/",
        views.get_contact_page_settings,
        name="get-contact-page-settings",
    ),  # Keep existing endpoint
    # Newsletter API (NEW)
    path("newsletter/", views.newsletter_signup, name="newsletter-signup"),
    # Health Check (NEW)
    path("health/", views.health_check, name="health-check"),
]
