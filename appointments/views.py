# appointments/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from datetime import datetime, timedelta
from checkout.models import Order
from .signals import send_appointment_updated_email
from .serializers import AppointmentSettingsSerializer, CalendarSettingsSerializer

from .models import (
    CalendarUser,
    AppointmentType,
    Availability,
    Appointment,
    AppointmentSettings,
    CalendarSettings,
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

            serializer = self.get_serializer(appointment)
            return Response(serializer.data)

        return Response(
            {"error": "Appointment cannot be cancelled"},
            status=status.HTTP_400_BAD_REQUEST,
        )


# Public API endpoints (no authentication required for booking)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_calendar_info(request):
    """
    Get calendar information for booking (single user system)
    """
    try:
        # Get the first active calendar user (since it's single user)
        calendar_user = (
            CalendarUser.objects.select_related("user")
            .prefetch_related("appointment_types", "booking_settings")
            .filter(is_calendar_active=True)
            .first()
        )

        if not calendar_user:
            return Response(
                {"error": "No active calendar found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CalendarUserPublicSerializer(calendar_user)
        return Response(serializer.data)

    except Exception as e:
        return Response(
            {"error": f"Failed to load calendar: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def get_available_slots(request):
    """
    Get available time slots for booking
    """
    try:
        # Get the active calendar user
        calendar_user = CalendarUser.objects.filter(is_calendar_active=True).first()

        if not calendar_user:
            return Response(
                {"error": "No active calendar found"}, status=status.HTTP_404_NOT_FOUND
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
@permission_classes([IsAuthenticated])
def book_appointment(request):
    """
    Book an appointment - creates appointment and handles payment if needed
    """

    serializer = BookAppointmentSerializer(data=request.data)

    if serializer.is_valid():
        try:
            # Get appointment type to check if payment is required
            appointment_type = AppointmentType.objects.get(
                id=serializer.validated_data["appointment_type_id"]
            )

            # Create the appointment (status will be 'pending' initially)
            appointment_data = serializer.validated_data.copy()
            appointment_data["appointment_type"] = appointment_type

            # Calculate end time
            start_datetime = datetime.combine(
                appointment_data["date"], appointment_data["start_time"]
            )
            end_datetime = start_datetime + timedelta(
                minutes=appointment_type.duration_minutes
            )
            appointment_data["end_time"] = end_datetime.time()

            # Create appointment
            appointment = Appointment.objects.create(**appointment_data)

            # Check if payment is required
            if appointment_type.requires_payment and appointment_type.price:
                # Create order for paid appointment
                order = Order.objects.create(
                    user=request.user,
                    # Appointment-specific fields
                    appointment_type=appointment_type,
                    appointment_date=appointment.date,
                    appointment_start_time=appointment.start_time,
                    appointment_customer_name=appointment.customer_name,
                    appointment_customer_phone=appointment.customer_phone or "",
                    appointment_notes=appointment.customer_notes or "",
                    # Order totals
                    subtotal=appointment_type.price,
                    total=appointment_type.price,
                    # Mark as appointment order
                    has_digital_items=True,  # Appointments are "digital services"
                    has_physical_items=False,
                )

                # Link appointment to order (we'll add this field)
                appointment.order = order
                appointment.payment_required = True
                appointment.payment_amount = appointment_type.price
                appointment.save()

                # Return redirect to checkout
                return Response(
                    {
                        "success": True,
                        "appointment_id": appointment.id,
                        "requires_payment": True,
                        "checkout_url": f"/checkout/order/{order.id}/",
                        "message": "Appointment created. Please complete payment.",
                    },
                    status=status.HTTP_201_CREATED,
                )
            else:
                # Free appointment - confirm immediately
                appointment.status = "confirmed"
                appointment.confirmed_at = timezone.now()
                appointment.save()

                return Response(
                    {
                        "success": True,
                        "appointment_id": appointment.id,
                        "requires_payment": False,
                        "message": "Your appointment has been booked successfully!",
                    },
                    status=status.HTTP_201_CREATED,
                )

        except AppointmentType.DoesNotExist:
            return Response(
                {"error": "Invalid appointment type"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to create appointment: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def calculate_available_slots(calendar_user, appointment_type, start_date, end_date):
    """
    Calculate available time slots using weekly schedule + overrides
    """
    available_slots = []
    current_date = start_date

    while current_date <= end_date:
        # Check if this is a weekday the calendar is open
        weekday = current_date.weekday()  # 0=Monday, 6=Sunday

        if not calendar_user.is_available_on_day(weekday):
            current_date += timedelta(days=1)
            continue

        # Get default hours for this day
        day_start, day_end = calendar_user.get_day_hours(weekday)

        if not day_start or not day_end:
            current_date += timedelta(days=1)
            continue

        # Check for availability overrides for this specific date
        availability_overrides = Availability.objects.filter(
            calendar_user=calendar_user, date=current_date
        )

        # If there are overrides, use them instead of default schedule
        if availability_overrides.exists():
            available_periods = []
            for override in availability_overrides:
                if override.is_available:
                    available_periods.append((override.start_time, override.end_time))
        else:
            # Use default weekly schedule
            available_periods = [(day_start, day_end)]

        # Get existing appointments for this date
        existing_appointments = Appointment.objects.filter(
            appointment_type__calendar_user=calendar_user,
            date=current_date,
            status__in=["pending", "confirmed"],
        )

        # For each available period, calculate free time slots
        for period_start, period_end in available_periods:
            slot_start = datetime.combine(current_date, period_start)
            slot_end = datetime.combine(current_date, period_end)
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
@permission_classes([AllowAny])  # Changed from IsAuthenticated
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
            {"error": "Appointment not found or email doesn't match"},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["PUT", "PATCH"])
@permission_classes([AllowAny])  # New endpoint for editing
def update_customer_appointment(request, appointment_id):
    """
    Update appointment details (customer endpoint)
    """
    email = request.data.get("email")

    if not email:
        return Response(
            {"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        appointment = Appointment.objects.get(id=appointment_id, customer_email=email)

        # Check if appointment can be modified
        if not appointment.can_be_cancelled():  # Same logic for editing
            return Response(
                {
                    "error": "Appointment cannot be modified (too close to appointment time or already completed)"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Only allow updating certain fields
        allowed_fields = ["customer_name", "customer_phone", "customer_notes"]

        # Create update data with only allowed fields
        update_data = {}
        for field in allowed_fields:
            if field in request.data:
                update_data[field] = request.data[field]

        # Handle date/time changes (more complex - requires slot availability check)
        if "date" in request.data or "start_time" in request.data:
            new_date = request.data.get("date", appointment.date)
            new_start_time = request.data.get("start_time", appointment.start_time)

            # Convert string date to date object if needed
            if isinstance(new_date, str):
                new_date = datetime.strptime(new_date, "%Y-%m-%d").date()

            # Convert string time to time object if needed
            if isinstance(new_start_time, str):
                new_start_time = datetime.strptime(new_start_time, "%H:%M").time()

            # Check if the new slot is available
            conflicts = Appointment.objects.filter(
                appointment_type__calendar_user=appointment.appointment_type.calendar_user,
                date=new_date,
                status__in=["pending", "confirmed"],
            ).exclude(id=appointment.id)  # Exclude current appointment

            # Calculate new end time
            start_datetime = datetime.combine(new_date, new_start_time)
            end_datetime = start_datetime + timedelta(
                minutes=appointment.duration_minutes
            )
            new_end_time = end_datetime.time()

            # Check for conflicts
            for conflict in conflicts:
                if (
                    new_start_time < conflict.end_time
                    and new_end_time > conflict.start_time
                ):
                    return Response(
                        {"error": "The requested time slot is not available"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Check calendar availability (basic check - you may want to enhance this)
            weekday = new_date.weekday()
            if not appointment.appointment_type.calendar_user.is_available_on_day(
                weekday
            ):
                day_names = [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                    "Sunday",
                ]
                return Response(
                    {"error": f"Calendar is not available on {day_names[weekday]}s"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            update_data["date"] = new_date
            update_data["start_time"] = new_start_time
            update_data["end_time"] = new_end_time

        # Update the appointment
        for field, value in update_data.items():
            setattr(appointment, field, value)

        appointment.save()

        # After successful update in the view:
        if update_data:  # If any changes were made
            send_appointment_updated_email(appointment)

        serializer = CustomerAppointmentSerializer(appointment)
        return Response(
            {
                "success": True,
                "message": "Appointment updated successfully",
                "appointment": serializer.data,
            }
        )

    except Appointment.DoesNotExist:
        return Response(
            {"error": "Appointment not found"}, status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to update appointment: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["POST"])
@permission_classes([AllowAny])  # Changed from IsAuthenticated
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

            serializer = CustomerAppointmentSerializer(appointment)
            return Response(
                {
                    "success": True,
                    "message": "Appointment cancelled successfully",
                    "appointment": serializer.data,
                }
            )
        else:
            return Response(
                {
                    "error": "Appointment cannot be cancelled (too close to appointment time or already completed)"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Appointment.DoesNotExist:
        return Response(
            {"error": "Appointment not found"}, status=status.HTTP_404_NOT_FOUND
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def get_available_slots_for_reschedule(request, appointment_id):
    """
    Get available slots for rescheduling an existing appointment
    """
    email = request.query_params.get("email")

    if not email:
        return Response(
            {"error": "Email parameter is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        appointment = Appointment.objects.get(id=appointment_id, customer_email=email)

        # Get the calendar user and appointment type
        calendar_user = appointment.appointment_type.calendar_user
        appointment_type = appointment.appointment_type

        # Get date range (next 30 days or calendar's booking window)
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=calendar_user.booking_window_days)

        # Calculate available slots (excluding current appointment)
        available_slots = calculate_available_slots_excluding_appointment(
            calendar_user, appointment_type, start_date, end_date, appointment.id
        )

        serializer = AvailableSlotSerializer(available_slots, many=True)
        return Response(serializer.data)

    except Appointment.DoesNotExist:
        return Response(
            {"error": "Appointment not found"}, status=status.HTTP_404_NOT_FOUND
        )


def calculate_available_slots_excluding_appointment(
    calendar_user, appointment_type, start_date, end_date, exclude_appointment_id
):
    """
    Modified version of calculate_available_slots that excludes a specific appointment
    """
    available_slots = []
    current_date = start_date

    while current_date <= end_date:
        # Check if this is a weekday the calendar is open
        weekday = current_date.weekday()

        if not calendar_user.is_available_on_day(weekday):
            current_date += timedelta(days=1)
            continue

        # Get default hours for this day
        day_start, day_end = calendar_user.get_day_hours(weekday)

        if not day_start or not day_end:
            current_date += timedelta(days=1)
            continue

        # Check for availability overrides
        availability_overrides = Availability.objects.filter(
            calendar_user=calendar_user, date=current_date
        )

        if availability_overrides.exists():
            available_periods = []
            for override in availability_overrides:
                if override.is_available:
                    available_periods.append((override.start_time, override.end_time))
        else:
            available_periods = [(day_start, day_end)]

        # Get existing appointments for this date (excluding the one being rescheduled)
        existing_appointments = Appointment.objects.filter(
            appointment_type__calendar_user=calendar_user,
            date=current_date,
            status__in=["pending", "confirmed"],
        ).exclude(id=exclude_appointment_id)

        # Calculate free time slots
        for period_start, period_end in available_periods:
            slot_start = datetime.combine(current_date, period_start)
            slot_end = datetime.combine(current_date, period_end)
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

                current_slot_start = slot_end_time + buffer_time

        current_date += timedelta(days=1)

    return available_slots


class AppointmentSettingsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for appointment page settings (read-only)
    """

    serializer_class = AppointmentSettingsSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return AppointmentSettings.objects.all()

    def list(self, request, *args, **kwargs):
        """Return the single settings instance as detail"""
        settings = AppointmentSettings.get_settings()
        serializer = self.get_serializer(settings)
        return Response(serializer.data)


class CalendarSettingsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for calendar page settings (read-only)
    """

    serializer_class = CalendarSettingsSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return CalendarSettings.objects.all()

    def list(self, request, *args, **kwargs):
        """Return the single settings instance as detail"""
        settings = CalendarSettings.get_settings()
        serializer = self.get_serializer(settings)
        return Response(serializer.data)
