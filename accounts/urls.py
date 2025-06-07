# accounts/urls.py
from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("change-password/", views.change_password, name="change_password"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path(
        "wishlist/add/<uuid:product_id>/", views.add_to_wishlist, name="add_to_wishlist"
    ),
    path(
        "wishlist/remove/<uuid:product_id>/",
        views.remove_from_wishlist,
        name="remove_from_wishlist",
    ),
    path("auth/verify-email/", views.verify_email_page, name="verify-email"),
    path(
        "auth/verify-email/<str:token>/",
        views.verify_email_token,
        name="verify-email-token",
    ),
    path(
        "auth/resend-verification/",
        views.resend_verification,
        name="resend-verification",
    ),
    path("auth/forgot-password/", views.forgot_password, name="forgot-password"),
    path(
        "auth/reset-password/<str:token>/", views.reset_password, name="reset-password"
    ),
]
