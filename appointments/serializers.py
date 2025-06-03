# appointments/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    CalendarUser,
    AppointmentType,
    Availability,
    Appointment,
    BookingSettings,
)
from datetime import datetime, timedelta, time
from django.utils import timezone

User = get_user_model()


class CalendarUserSerializer(serializers.ModelSerializer):
    """Serializer for calendar user profiles"""

    username = serializers.CharField(source="user.username", read_only=True)
    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = CalendarUser
        fields = [
            "id",
            "username",
            "business_name",
            "display_name",
            "timezone",
            "booking_window_days",
            "buffer_minutes",
            "is_calendar_active",
            "booking_instructions",
        ]
        read_only_fields = ["id"]


class AppointmentTypeSerializer(serializers.ModelSerializer):
    """Serializer for appointment types"""

    class Meta:
        model = AppointmentType
        fields = [
            "id",
            "name",
            "description",
            "duration_minutes",
            "price",
            "color",
            "is_active",
            "requires_payment",
            "order",
        ]
        read_only_fields = ["id"]


class AppointmentTypeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing appointment types"""

    class Meta:
        model = AppointmentType
        fields = [
            "id",
            "name",
            "duration_minutes",
            "price",
            "color",
            "requires_payment",
        ]


class AvailabilitySerializer(serializers.ModelSerializer):
    """Serializer for availability slots"""

    class Meta:
        model = Availability
        fields = [
            "id",
            "date",
            "start_time",
            "end_time",
            "is_available",
            "recurring_pattern",
            "recurring_until",
            "notes",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        """Validate availability data"""
        if data["start_time"] >= data["end_time"]:
            raise serializers.ValidationError("Start time must be before end time")
        return data


class AvailableSlotSerializer(serializers.Serializer):
    """Serializer for available time slots"""

    date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    appointment_type_id = serializers.IntegerField()


class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer for appointments"""

    appointment_type_name = serializers.CharField(
        source="appointment_type.name", read_only=True
    )
    calendar_user = serializers.CharField(
        source="appointment_type.calendar_user.display_name", read_only=True
    )
    duration_minutes = serializers.IntegerField(read_only=True)
    can_be_cancelled = serializers.BooleanField(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "appointment_type",
            "appointment_type_name",
            "calendar_user",
            "customer_name",
            "customer_email",
            "customer_phone",
            "date",
            "start_time",
            "end_time",
            "duration_minutes",
            "status",
            "customer_notes",
            "payment_required",
            "payment_status",
            "payment_amount",
            "can_be_cancelled",
            "created_at",
            "confirmed_at",
        ]
        read_only_fields = [
            "id",
            "end_time",
            "payment_required",
            "payment_amount",
            "created_at",
            "confirmed_at",
        ]

    def validate(self, data):
        """Validate appointment data"""
        appointment_type = data["appointment_type"]
        date = data["date"]
        start_time = data["start_time"]

        # Check if booking is within allowed window
        calendar_user = appointment_type.calendar_user
        max_advance_date = timezone.now().date() + timedelta(
            days=calendar_user.booking_window_days
        )

        if date > max_advance_date:
            raise serializers.ValidationError(
                f"Bookings are only allowed up to {calendar_user.booking_window_days} days in advance"
            )

        # Check minimum notice
        booking_settings = getattr(calendar_user, "booking_settings", None)
        if booking_settings:
            min_notice_datetime = timezone.now() + timedelta(
                hours=booking_settings.min_notice_hours
            )
            appointment_datetime = timezone.make_aware(
                datetime.combine(date, start_time)
            )

            if appointment_datetime < min_notice_datetime:
                raise serializers.ValidationError(
                    f"Minimum {booking_settings.min_notice_hours} hours notice required"
                )

        return data

    def create(self, validated_data):
        """Create appointment with calculated end time"""
        appointment_type = validated_data["appointment_type"]
        start_datetime = datetime.combine(
            validated_data["date"], validated_data["start_time"]
        )
        end_datetime = start_datetime + timedelta(
            minutes=appointment_type.duration_minutes
        )
        validated_data["end_time"] = end_datetime.time()

        return super().create(validated_data)


class BookAppointmentSerializer(serializers.Serializer):
    """Serializer for booking appointments (public API)"""

    appointment_type_id = serializers.IntegerField()
    customer_name = serializers.CharField(max_length=200)
    customer_email = serializers.EmailField()
    customer_phone = serializers.CharField(
        max_length=20, required=False, allow_blank=True
    )
    date = serializers.DateField()
    start_time = serializers.TimeField()
    customer_notes = serializers.CharField(required=False, allow_blank=True)

    def validate_appointment_type_id(self, value):
        """Validate appointment type exists and is active"""
        try:
            appointment_type = AppointmentType.objects.get(id=value, is_active=True)
            return value
        except AppointmentType.DoesNotExist:
            raise serializers.ValidationError("Invalid appointment type")

    def validate(self, data):
        """Validate booking data"""
        appointment_type = AppointmentType.objects.get(id=data["appointment_type_id"])
        date = data["date"]
        start_time = data["start_time"]

        # Check if date is in the past
        if date < timezone.now().date():
            raise serializers.ValidationError("Cannot book appointments in the past")

        # Check if time slot is available
        # This would typically check against existing appointments and availability
        # For now, we'll do basic validation

        return data

    def create(self, validated_data):
        """Create the appointment"""
        appointment_type = AppointmentType.objects.get(
            id=validated_data.pop("appointment_type_id")
        )

        # Calculate end time
        start_datetime = datetime.combine(
            validated_data["date"], validated_data["start_time"]
        )
        end_datetime = start_datetime + timedelta(
            minutes=appointment_type.duration_minutes
        )

        appointment = Appointment.objects.create(
            appointment_type=appointment_type,
            end_time=end_datetime.time(),
            **validated_data,
        )

        return appointment


class BookingSettingsSerializer(serializers.ModelSerializer):
    """Serializer for booking settings"""

    class Meta:
        model = BookingSettings
        fields = [
            "min_notice_hours",
            "max_bookings_per_day",
            "booking_page_title",
            "booking_page_description",
            "success_message",
        ]


class CalendarUserPublicSerializer(serializers.ModelSerializer):
    """Public serializer for calendar user (for booking pages)"""

    username = serializers.CharField(source="user.username", read_only=True)
    display_name = serializers.CharField(read_only=True)
    appointment_types = AppointmentTypeListSerializer(many=True, read_only=True)
    booking_settings = BookingSettingsSerializer(read_only=True)

    class Meta:
        model = CalendarUser
        fields = [
            "username",
            "business_name",
            "display_name",
            "timezone",
            "booking_instructions",
            "appointment_types",
            "booking_settings",
        ]


class CustomerAppointmentSerializer(serializers.ModelSerializer):
    """Serializer for customer viewing their appointments"""

    appointment_type_name = serializers.CharField(
        source="appointment_type.name", read_only=True
    )
    calendar_user_name = serializers.CharField(
        source="appointment_type.calendar_user.display_name", read_only=True
    )
    duration_minutes = serializers.IntegerField(read_only=True)
    can_be_cancelled = serializers.BooleanField(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "appointment_type_name",
            "calendar_user_name",
            "date",
            "start_time",
            "end_time",
            "duration_minutes",
            "status",
            "customer_notes",
            "payment_status",
            "payment_amount",
            "can_be_cancelled",
            "created_at",
            "confirmed_at",
        ]
        read_only_fields = "__all__"
