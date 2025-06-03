# appointments/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for authenticated API endpoints
router = DefaultRouter()
router.register(r"profiles", views.CalendarUserViewSet, basename="calendar-user")
router.register(
    r"appointment-types", views.AppointmentTypeViewSet, basename="appointment-type"
)
router.register(r"availability", views.AvailabilityViewSet, basename="availability")
router.register(r"appointments", views.AppointmentViewSet, basename="appointment")

app_name = "appointments"

urlpatterns = [
    # Authenticated API endpoints
    path("api/", include(router.urls)),
    # Public booking API endpoints
    path(
        "api/public/<str:username>/",
        views.get_calendar_user,
        name="public-calendar-user",
    ),
    path(
        "api/public/<str:username>/slots/",
        views.get_available_slots,
        name="available-slots",
    ),
    path("api/public/book/", views.book_appointment, name="book-appointment"),
    path(
        "api/public/appointment/<int:appointment_id>/",
        views.get_customer_appointment,
        name="customer-appointment",
    ),
    path(
        "api/public/appointment/<int:appointment_id>/cancel/",
        views.cancel_customer_appointment,
        name="cancel-appointment",
    ),
]
