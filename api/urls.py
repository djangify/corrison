# Update api/urls.py to include auth endpoints
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from accounts.views import WishlistViewSet
from blog.views import BlogPostViewSet
from linkhub.views import LinkHubViewSet
from pages.views import PageViewSet, TestimonialViewSet
from accounts import api_views as auth_views
from checkout.views import OrderSettingsViewSet
from cart.views import CartViewSet, CartItemViewSet
from appointments.views import (
    CalendarUserViewSet,
    CalendarSettingsViewSet,
    AppointmentSettingsViewSet,
    AppointmentTypeViewSet,
    AvailabilityViewSet,
    AppointmentViewSet,
)
from courses.views import (
    CategoryViewSet as CourseCategoryViewSet,
    CourseViewSet,
    EnrollmentViewSet,
    CourseSettingsViewSet,
)

from . import views

# Import appointment views for public endpoints
from appointments import views as appointments_views

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
router.register(
    r"appointment-settings", AppointmentSettingsViewSet, basename="appointment-settings"
)
router.register(
    r"calendar-settings", CalendarSettingsViewSet, basename="calendar-settings"
)
router.register(r"order-settings", OrderSettingsViewSet, basename="order-settings")

# Appointments endpoints (authenticated - for calendar owners)
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

# Courses endpoints
router.register(
    r"courses/categories", CourseCategoryViewSet, basename="course-category"
)
router.register(r"courses", CourseViewSet, basename="course")
router.register(r"enrollments", EnrollmentViewSet, basename="enrollment")
router.register(r"courses-settings", CourseSettingsViewSet, basename="courses-settings")

urlpatterns = [
    path("", include(router.urls)),
    # Authentication endpoints
    path("auth/register/", auth_views.register, name="auth-register"),
    path("auth/login/", auth_views.login, name="auth-login"),
    path("auth/logout/", auth_views.logout, name="auth-logout"),
    path(
        "auth/resend-verification/",
        auth_views.resend_verification,
        name="resend-verification",
    ),
    path("auth/profile/", auth_views.user_profile, name="user-profile"),
    path("auth/change-password/", auth_views.change_password, name="change-password"),
    # Existing custom API endpoints
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
    # Get calendar info (replaces username-specific endpoint)
    path(
        "calendar/info/",
        appointments_views.get_calendar_info,
        name="calendar-info",
    ),
    # Get available slots for booking
    path(
        "calendar/slots/",
        appointments_views.get_available_slots,
        name="available-slots",
    ),
    # Book an appointment
    path(
        "calendar/book/",
        appointments_views.book_appointment,
        name="book-appointment",
    ),
    # Customer appointment management (requires email verification)
    path(
        "calendar/appointment/<int:appointment_id>/",
        appointments_views.get_customer_appointment,
        name="customer-appointment",
    ),
    # Update appointment endpoint
    path(
        "calendar/appointment/<int:appointment_id>/update/",
        appointments_views.update_customer_appointment,
        name="update-customer-appointment",
    ),
    # Updated: Cancel appointment endpoint
    path(
        "calendar/appointment/<int:appointment_id>/cancel/",
        appointments_views.cancel_customer_appointment,
        name="cancel-appointment",
    ),
    path(
        "calendar/appointment/<int:appointment_id>/update/",
        appointments_views.update_customer_appointment,
        name="update-appointment",
        # Get available slots for rescheduling
    ),
    path(
        "calendar/appointment/<int:appointment_id>/available-slots/",
        appointments_views.get_available_slots_for_reschedule,
        name="reschedule-slots",
    ),
]
