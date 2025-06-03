# Update api/urls.py to include calendar API endpoints

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from accounts.views import WishlistViewSet
from blog.views import BlogPostViewSet
from linkhub.views import LinkHubViewSet
from pages.views import PageViewSet, TestimonialViewSet
from cart.views import CartViewSet, CartItemViewSet
from appointments.views import (
    CalendarUserViewSet,
    AppointmentTypeViewSet,
    AvailabilityViewSet,
    AppointmentViewSet,
)  # ADD THIS
from . import views

# Register viewsets with router
router = DefaultRouter()
router.register(r"wishlist", WishlistViewSet, basename="wishlist")
router.register(r"products", views.ProductViewSet, basename="product")
router.register(r"categories", views.CategoryViewSet, basename="category")
router.register(r"orders", views.OrderViewSet, basename="order")
router.register(r"payments", views.PaymentViewSet, basename="payment")
router.register(r"users", views.UserViewSet, basename="user")
router.register(r"blog/posts", BlogPostViewSet, basename="blog")
router.register(r"pages", PageViewSet, basename="page")
router.register(r"testimonials", TestimonialViewSet, basename="testimonial")
router.register(r"linkhubs", LinkHubViewSet, basename="linkhub")
router.register(r"cart", CartViewSet, basename="cart")
router.register(r"items", CartItemViewSet, basename="cart-item")

# ADD THESE APPOINTMENTS ENDPOINTS
router.register(r"appointments/profiles", CalendarUserViewSet, basename="calendar-user")
router.register(
    r"appointments/appointment-types",
    AppointmentTypeViewSet,
    basename="appointment-type",
)
router.register(
    r"appointments/availability", AvailabilityViewSet, basename="availability"
)
router.register(
    r"appointments/appointments", AppointmentViewSet, basename="appointment"
)

urlpatterns = [
    path("", include(router.urls)),
    # Custom API endpoints
    path("cart/add/", views.add_to_cart, name="add-to-cart"),
    path("cart/update/", views.update_cart_item, name="update-cart-item"),
    path("cart/remove/", views.remove_cart_item, name="remove-cart-item"),
    path("", include("core.urls")),
    path(
        "create-payment-intent/",
        views.create_payment_intent,
        name="create-payment-intent",
    ),
    path("create-order/", views.create_order, name="create-order"),
    path(
        "placeholder/<int:width>/<int:height>/",
        views.placeholder_image,
        name="placeholder-image",
    ),
    # ADD APPOINTMENTS PUBLIC API ENDPOINTS
    path("appointments/", include("appointments.urls")),
]
