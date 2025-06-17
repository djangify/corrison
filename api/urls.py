# api/urls.py - Updated for checkout with account registration
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from accounts.views import WishlistViewSet
from blog.views import BlogPostViewSet
from linkhub.views import LinkHubViewSet
from pages.views import PageViewSet, TestimonialViewSet
from accounts import api_views as auth_views
from checkout.views import check_payment_status, OrderSettingsViewSet
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

from checkout.webhooks import stripe_webhook
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
router.register(r"blog/posts", BlogPostViewSet, basename="blog")
router.register(r"pages", PageViewSet, basename="page")
router.register(r"testimonials", TestimonialViewSet, basename="testimonial")
router.register(r"linkhubs", LinkHubViewSet, basename="linkhub")

# CART ENDPOINTS - Simplified for digital-only
router.register(r"cart", CartViewSet, basename="cart")
router.register(r"items", CartItemViewSet, basename="cart-item")

# Settings endpoints
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
router.register(r"course-settings", CourseSettingsViewSet, basename="course-settings")

urlpatterns = [
    path("", include(router.urls)),
    # Authentication endpoints
    path("auth/register/", auth_views.register, name="auth-register"),
    path("auth/login/", auth_views.login, name="auth-login"),
    path("auth/logout/", auth_views.logout, name="auth-logout"),
    path(
        "auth/verify-email/<str:token>/", auth_views.verify_email, name="verify-email"
    ),
    path(
        "auth/resend-verification/",
        auth_views.resend_verification,
        name="resend-verification",
    ),
    path("auth/profile/", auth_views.user_profile, name="user-profile"),
    path("auth/change-password/", auth_views.change_password, name="change-password"),
    # Checkout endpoints
    path("check-email/", views.check_email, name="check-email"),
    path(
        "create-payment-intent/",
        views.create_payment_intent,
        name="create-payment-intent",
    ),
    path("create-order/", views.create_order, name="create-order"),
    path("check-payment-status/", check_payment_status, name="check-payment-status"),
    path("stripe/webhook/", stripe_webhook, name="stripe-webhook"),
    # Placeholder image
    path(
        "placeholder/<int:width>/<int:height>/",
        views.placeholder_image,
        name="placeholder-image",
    ),
    # Core includes
    path("", include("core.urls")),
    # ============================================================
    # APPOINTMENTS PUBLIC API - SINGLE USER SYSTEM (NO USERNAME)
    # ============================================================
    # RESTORED: Original calendar endpoints exactly as frontend expects
    path(
        "calendar/info/",
        appointments_views.get_calendar_info,
        name="calendar-info",
    ),
    path(
        "calendar/slots/",
        appointments_views.get_available_slots,
        name="calendar-slots",
    ),
    path(
        "calendar/book/",
        appointments_views.book_appointment,
        name="calendar-book",
    ),
    # RESTORED: Customer appointments endpoint
    path(
        "my-appointments/",
        appointments_views.get_my_appointments,
        name="my-appointments",
    ),
    # Customer appointment management (requires email verification)
    # This handles the ?id=X format from emails
    path(
        "calendar/appointment/",
        appointments_views.get_customer_appointment_query,
        name="customer-appointment-query",
    ),
    path(
        "calendar/appointment/<int:appointment_id>",
        appointments_views.get_customer_appointment,
        name="customer-appointment-detail",
    ),
    path(
        "calendar/appointment/<int:appointment_id>/",
        appointments_views.get_customer_appointment,
        name="customer-appointment",
    ),
    path(
        "calendar/appointment/<int:appointment_id>/update/",
        appointments_views.update_customer_appointment,
        name="update-customer-appointment",
    ),
    path(
        "calendar/appointment/<int:appointment_id>/cancel/",
        appointments_views.cancel_customer_appointment,
        name="cancel-appointment",
    ),
    path(
        "calendar/appointment/<int:appointment_id>/available-slots/",
        appointments_views.get_available_slots_for_reschedule,
        name="reschedule-slots",
    ),
    # COURSES PUBLIC API (LMS functionality)
    path(
        "courses/featured/",
        CourseViewSet.as_view({"get": "featured"}),
        name="featured-courses",
    ),
    path(
        "courses/<slug:slug>/",
        CourseViewSet.as_view({"get": "retrieve"}),
        name="course-detail",
    ),
    path(
        "courses/<slug:slug>/enroll/",
        EnrollmentViewSet.as_view({"post": "enroll"}),
        name="course-enroll",
    ),
]
