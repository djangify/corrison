# appointments/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

# from django.shortcuts import get_object_or_404
from django.utils import timezone

# from django.db.models import Q
from datetime import datetime, timedelta
# import pytz

from .models import (
    CalendarUser,
    AppointmentType,
    Availability,
    Appointment,
    # BookingSettings,
)
from .serializers import (
    CalendarUserSerializer,
    CalendarUserPublicSerializer,
    AppointmentTypeSerializer,
    AvailabilitySerializer,
    AppointmentSerializer,
    BookAppointmentSerializer,
    CustomerAppointmentSerializer,
    AvailableSlotSerializer,
    # BookingSettingsSerializer,
)


class CalendarUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for calendar users (authenticated users managing their calendar)
    """

    serializer_class = CalendarUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return only the current user's calendar profile"""
        return CalendarUser.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Create calendar profile for current user"""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["get"])
    def appointments(self, request, pk=None):
        """Get all appointments for this calendar user"""
        calendar_user = self.get_object()
        appointments = Appointment.objects.filter(
            appointment_type__calendar_user=calendar_user
        ).order_by("date", "start_time")

        # Filter by date range if provided
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if start_date:
            appointments = appointments.filter(date__gte=start_date)
        if end_date:
            appointments = appointments.filter(date__lte=end_date)

        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        """Get calendar statistics"""
        calendar_user = self.get_object()

        # Get appointment counts
        total_appointments = Appointment.objects.filter(
            appointment_type__calendar_user=calendar_user
        ).count()

        confirmed_appointments = Appointment.objects.filter(
            appointment_type__calendar_user=calendar_user, status="confirmed"
        ).count()

        pending_appointments = Appointment.objects.filter(
            appointment_type__calendar_user=calendar_user, status="pending"
        ).count()

        # Get this week's appointments
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        this_week_appointments = Appointment.objects.filter(
            appointment_type__calendar_user=calendar_user,
            date__range=[week_start, week_end],
        ).count()

        return Response(
            {
                "total_appointments": total_appointments,
                "confirmed_appointments": confirmed_appointments,
                "pending_appointments": pending_appointments,
                "this_week_appointments": this_week_appointments,
            }
        )


class AppointmentTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for appointment types
    """

    serializer_class = AppointmentTypeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return appointment types for current user's calendar"""
        try:
            calendar_user = CalendarUser.objects.get(user=self.request.user)
            return AppointmentType.objects.filter(calendar_user=calendar_user)
        except CalendarUser.DoesNotExist:
            return AppointmentType.objects.none()

    def perform_create(self, serializer):
        """Create appointment type for current user's calendar"""
        calendar_user, created = CalendarUser.objects.get_or_create(
            user=self.request.user
        )
        serializer.save(calendar_user=calendar_user)


class AvailabilityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for availability management
    """

    serializer_class = AvailabilitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return availability for current user's calendar"""
        try:
            calendar_user = CalendarUser.objects.get(user=self.request.user)
            return Availability.objects.filter(calendar_user=calendar_user)
        except CalendarUser.DoesNotExist:
            return Availability.objects.none()

    def perform_create(self, serializer):
        """Create availability for current user's calendar"""
        calendar_user, created = CalendarUser.objects.get_or_create(
            user=self.request.user
        )
        serializer.save(calendar_user=calendar_user)


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for appointment management (calendar owner view)
    """

    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return appointments for current user's calendar"""
        try:
            calendar_user = CalendarUser.objects.get(user=self.request.user)
            return Appointment.objects.filter(
                appointment_type__calendar_user=calendar_user
            ).order_by("date", "start_time")
        except CalendarUser.DoesNotExist:
            return Appointment.objects.none()

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """Confirm an appointment"""
        appointment = self.get_object()
        if appointment.status == "pending":
            appointment.status = "confirmed"
            appointment.confirmed_at = timezone.now()
            appointment.save()

            # TODO: Send confirmation email to customer

            serializer = self.get_serializer(appointment)
            return Response(serializer.data)

        return Response(
            {"error": "Appointment cannot be confirmed"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel an appointment"""
        appointment = self.get_object()
        if appointment.can_be_cancelled():
            appointment.status = "cancelled"
            appointment.cancelled_at = timezone.now()
            appointment.save()

            # TODO: Send cancellation email to customer

            serializer = self.get_serializer(appointment)
            return Response(serializer.data)

        return Response(
            {"error": "Appointment cannot be cancelled"},
            status=status.HTTP_400_BAD_REQUEST,
        )


# Public API endpoints (no authentication required)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_calendar_user(request, username):
    """
    Get public calendar information for a user
    """
    try:
        calendar_user = (
            CalendarUser.objects.select_related("user")
            .prefetch_related("appointment_types", "booking_settings")
            .get(user__username=username, is_calendar_active=True)
        )

        serializer = CalendarUserPublicSerializer(calendar_user)
        return Response(serializer.data)

    except CalendarUser.DoesNotExist:
        return Response(
            {"error": "Calendar not found or not active"},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def get_available_slots(request, username):
    """
    Get available time slots for a calendar user
    """
    try:
        calendar_user = CalendarUser.objects.get(
            user__username=username, is_calendar_active=True
        )
    except CalendarUser.DoesNotExist:
        return Response(
            {"error": "Calendar not found"}, status=status.HTTP_404_NOT_FOUND
        )

    # Get query parameters
    start_date = request.query_params.get("start_date")
    end_date = request.query_params.get("end_date")
    appointment_type_id = request.query_params.get("appointment_type_id")

    if not start_date:
        start_date = timezone.now().date()
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

    if not end_date:
        end_date = start_date + timedelta(days=calendar_user.booking_window_days)
    else:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    # Get appointment type
    if appointment_type_id:
        try:
            appointment_type = AppointmentType.objects.get(
                id=appointment_type_id, calendar_user=calendar_user, is_active=True
            )
        except AppointmentType.DoesNotExist:
            return Response(
                {"error": "Invalid appointment type"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    else:
        return Response(
            {"error": "appointment_type_id is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Calculate available slots
    available_slots = calculate_available_slots(
        calendar_user, appointment_type, start_date, end_date
    )

    serializer = AvailableSlotSerializer(available_slots, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([AllowAny])
def book_appointment(request):
    """
    Book an appointment (public endpoint)
    """
    serializer = BookAppointmentSerializer(data=request.data)

    if serializer.is_valid():
        try:
            appointment = serializer.save()

            # TODO: Send confirmation email
            # TODO: If payment required, create Stripe payment intent

            response_serializer = CustomerAppointmentSerializer(appointment)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": f"Failed to create appointment: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_customer_appointment(request, appointment_id):
    """
    Get appointment details for customer (requires email verification)
    """
    email = request.query_params.get("email")

    if not email:
        return Response(
            {"error": "Email parameter is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        appointment = Appointment.objects.get(id=appointment_id, customer_email=email)

        serializer = CustomerAppointmentSerializer(appointment)
        return Response(serializer.data)

    except Appointment.DoesNotExist:
        return Response(
            {"error": "Appointment not found"}, status=status.HTTP_404_NOT_FOUND
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def cancel_customer_appointment(request, appointment_id):
    """
    Cancel appointment (customer endpoint)
    """
    email = request.data.get("email")

    if not email:
        return Response(
            {"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        appointment = Appointment.objects.get(id=appointment_id, customer_email=email)

        if appointment.can_be_cancelled():
            appointment.status = "cancelled"
            appointment.cancelled_at = timezone.now()
            appointment.save()

            # TODO: Send cancellation confirmation email

            serializer = CustomerAppointmentSerializer(appointment)
            return Response(serializer.data)
        else:
            return Response(
                {"error": "Appointment cannot be cancelled"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Appointment.DoesNotExist:
        return Response(
            {"error": "Appointment not found"}, status=status.HTTP_404_NOT_FOUND
        )


def calculate_available_slots(calendar_user, appointment_type, start_date, end_date):
    """
    Calculate available time slots for a given period
    """
    available_slots = []
    current_date = start_date

    while current_date <= end_date:
        # Get availability for this date
        availability_slots = Availability.objects.filter(
            calendar_user=calendar_user, date=current_date, is_available=True
        )

        # Get existing appointments for this date
        existing_appointments = Appointment.objects.filter(
            appointment_type__calendar_user=calendar_user,
            date=current_date,
            status__in=["pending", "confirmed"],
        )

        # For each availability slot, calculate free time slots
        for availability in availability_slots:
            slot_start = datetime.combine(current_date, availability.start_time)
            slot_end = datetime.combine(current_date, availability.end_time)
            duration = timedelta(minutes=appointment_type.duration_minutes)
            buffer_time = timedelta(minutes=calendar_user.buffer_minutes)

            current_slot_start = slot_start

            while current_slot_start + duration <= slot_end:
                slot_end_time = current_slot_start + duration

                # Check if this slot conflicts with existing appointments
                conflicts = existing_appointments.filter(
                    start_time__lt=slot_end_time.time(),
                    end_time__gt=current_slot_start.time(),
                )

                if not conflicts.exists():
                    available_slots.append(
                        {
                            "date": current_date,
                            "start_time": current_slot_start.time(),
                            "end_time": slot_end_time.time(),
                            "appointment_type_id": appointment_type.id,
                        }
                    )

                # Move to next possible slot (including buffer time)
                current_slot_start = slot_end_time + buffer_time

        current_date += timedelta(days=1)

    return available_slots


@api_view(["GET"])
@permission_classes([AllowAny])
def get_default_calendar(request):
    """
    Get the first active calendar user as default
    """
    try:
        # Get the first active calendar user
        calendar_user = (
            CalendarUser.objects.filter(is_calendar_active=True)
            .select_related("user")
            .first()
        )

        if not calendar_user:
            return Response(
                {"error": "No active calendars available"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "username": calendar_user.user.username,
                "display_name": calendar_user.display_name,
                "business_name": calendar_user.business_name,
            }
        )

    except Exception:
        return Response(
            {"error": "Failed to load default calendar"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
