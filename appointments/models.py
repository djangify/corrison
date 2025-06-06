# appointments/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta, time

User = get_user_model()


class CalendarUser(models.Model):
    """
    Extended user profile for calendar functionality - Single User System
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="calendar_profile"
    )
    business_name = models.CharField(max_length=200, blank=True)
    timezone = models.CharField(
        max_length=50,
        default="UTC",
        help_text="Timezone for this user's calendar (e.g., 'America/New_York')",
    )
    booking_window_days = models.PositiveIntegerField(
        default=30, help_text="How many days in advance customers can book"
    )
    buffer_minutes = models.PositiveIntegerField(
        default=15, help_text="Buffer time between appointments in minutes"
    )
    is_calendar_active = models.BooleanField(
        default=True, help_text="Whether this calendar is accepting bookings"
    )
    booking_instructions = models.TextField(
        blank=True, help_text="Instructions shown to customers when booking"
    )

    # Default weekly availability - proper fields instead of JSON
    monday_enabled = models.BooleanField(default=True)
    monday_start = models.TimeField(default=time(9, 0))  # 9:00 AM
    monday_end = models.TimeField(default=time(17, 0))  # 5:00 PM

    tuesday_enabled = models.BooleanField(default=True)
    tuesday_start = models.TimeField(default=time(9, 0))
    tuesday_end = models.TimeField(default=time(17, 0))

    wednesday_enabled = models.BooleanField(default=True)
    wednesday_start = models.TimeField(default=time(9, 0))
    wednesday_end = models.TimeField(default=time(17, 0))

    thursday_enabled = models.BooleanField(default=True)
    thursday_start = models.TimeField(default=time(9, 0))
    thursday_end = models.TimeField(default=time(17, 0))

    friday_enabled = models.BooleanField(default=True)
    friday_start = models.TimeField(default=time(9, 0))
    friday_end = models.TimeField(default=time(17, 0))

    saturday_enabled = models.BooleanField(default=False)
    saturday_start = models.TimeField(default=time(10, 0))  # 10:00 AM
    saturday_end = models.TimeField(default=time(15, 0))  # 3:00 PM

    sunday_enabled = models.BooleanField(default=False)
    sunday_start = models.TimeField(default=time(12, 0))  # 12:00 PM
    sunday_end = models.TimeField(default=time(16, 0))  # 4:00 PM

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Calendar User"
        verbose_name_plural = "Calendar Users"

    def __str__(self):
        return f"{self.user.username} - {self.business_name or 'Calendar'}"

    @property
    def display_name(self):
        """Return business name or username for display"""
        return self.business_name or self.user.get_full_name() or self.user.username

    def get_day_availability(self, day_name):
        """Get availability for a specific day of the week"""
        day_name = day_name.lower()
        if hasattr(self, f"{day_name}_enabled"):
            return {
                "enabled": getattr(self, f"{day_name}_enabled"),
                "start": getattr(self, f"{day_name}_start"),
                "end": getattr(self, f"{day_name}_end"),
            }
        return {"enabled": False, "start": None, "end": None}

    def is_available_on_day(self, weekday):
        """Check if calendar is available on a specific weekday (0=Monday, 6=Sunday)"""
        day_names = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]
        if 0 <= weekday <= 6:
            day_name = day_names[weekday]
            return getattr(self, f"{day_name}_enabled", False)
        return False

    def get_day_hours(self, weekday):
        """Get start/end hours for a specific weekday"""
        day_names = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]
        if 0 <= weekday <= 6:
            day_name = day_names[weekday]
            return (
                getattr(self, f"{day_name}_start", None),
                getattr(self, f"{day_name}_end", None),
            )
        return None, None


class AppointmentType(models.Model):
    """
    Types of appointments a user offers
    """

    calendar_user = models.ForeignKey(
        CalendarUser, on_delete=models.CASCADE, related_name="appointment_types"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Leave blank for free appointments",
    )
    color = models.CharField(
        max_length=7, default="#3B82F6", help_text="Hex color for calendar display"
    )
    is_active = models.BooleanField(default=True)
    requires_payment = models.BooleanField(
        default=False,
        help_text="Whether payment is required before booking confirmation",
    )
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Appointment Type"
        verbose_name_plural = "Appointment Types"

    def __str__(self):
        price_str = f" (${self.price})" if self.price else " (Free)"
        return f"{self.name} - {self.duration_minutes}min{price_str}"


class Availability(models.Model):
    """
    Specific availability for a calendar user (overrides default weekly schedule)
    """

    RECURRING_CHOICES = [
        ("none", "One-time only"),
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    ]

    calendar_user = models.ForeignKey(
        CalendarUser, on_delete=models.CASCADE, related_name="availability_slots"
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(
        default=True,
        help_text="False = blocked time, True = available time (overrides default schedule)",
    )
    recurring_pattern = models.CharField(
        max_length=10, choices=RECURRING_CHOICES, default="none"
    )
    recurring_until = models.DateField(
        null=True,
        blank=True,
        help_text="When recurring pattern ends (leave blank for indefinite)",
    )
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date", "start_time"]
        verbose_name = "Availability Override"
        verbose_name_plural = "Availability Overrides"
        unique_together = ["calendar_user", "date", "start_time", "end_time"]

    def __str__(self):
        status = "Available" if self.is_available else "Blocked"
        return f"{self.calendar_user.user.username} - {self.date} {self.start_time}-{self.end_time} ({status})"

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time")

        if self.recurring_pattern != "none" and not self.recurring_until:
            # Set default end date for recurring patterns
            if self.recurring_pattern == "weekly":
                self.recurring_until = self.date + timedelta(days=365)  # 1 year
            elif self.recurring_pattern == "daily":
                self.recurring_until = self.date + timedelta(days=30)  # 1 month
            elif self.recurring_pattern == "monthly":
                self.recurring_until = self.date + timedelta(days=365)  # 1 year


class Appointment(models.Model):
    """
    Booked appointments
    """

    STATUS_CHOICES = [
        ("pending", "Pending Confirmation"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
        ("no_show", "No Show"),
    ]

    appointment_type = models.ForeignKey(
        AppointmentType, on_delete=models.CASCADE, related_name="appointments"
    )

    # Customer information
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20, blank=True)

    # Appointment details
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    # Status and notes
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    customer_notes = models.TextField(
        blank=True, help_text="Notes from customer during booking"
    )
    admin_notes = models.TextField(
        blank=True, help_text="Internal notes for calendar owner"
    )

    # Payment information
    payment_required = models.BooleanField(default=False)
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ("not_required", "Not Required"),
            ("pending", "Payment Pending"),
            ("paid", "Paid"),
            ("refunded", "Refunded"),
        ],
        default="not_required",
    )
    payment_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    stripe_payment_intent_id = models.CharField(max_length=200, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["date", "start_time"]
        verbose_name = "Appointment"
        verbose_name_plural = "Appointments"

    def __str__(self):
        return f"{self.customer_name} - {self.appointment_type.name} - {self.date} {self.start_time}"

    @property
    def calendar_user(self):
        """Get the calendar user for this appointment"""
        return self.appointment_type.calendar_user

    @property
    def duration_minutes(self):
        """Get appointment duration in minutes"""
        return self.appointment_type.duration_minutes

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time")

        # Set end time based on appointment type duration
        start_datetime = datetime.combine(self.date, self.start_time)
        end_datetime = start_datetime + timedelta(
            minutes=self.appointment_type.duration_minutes
        )
        self.end_time = end_datetime.time()

    def save(self, *args, **kwargs):
        # Set payment fields based on appointment type
        if self.appointment_type.requires_payment and self.appointment_type.price:
            self.payment_required = True
            self.payment_amount = self.appointment_type.price
            if self.payment_status == "not_required":
                self.payment_status = "pending"

        # Set confirmed_at timestamp
        if self.status == "confirmed" and not self.confirmed_at:
            self.confirmed_at = timezone.now()

        # Set cancelled_at timestamp
        if self.status == "cancelled" and not self.cancelled_at:
            self.cancelled_at = timezone.now()

        super().save(*args, **kwargs)

    def can_be_cancelled(self):
        """Check if appointment can still be cancelled"""
        if self.status in ["cancelled", "completed", "no_show"]:
            return False

        # Can't cancel if appointment is in the past
        appointment_datetime = datetime.combine(self.date, self.start_time)
        return appointment_datetime > timezone.now()

    def get_absolute_url(self):
        """Get URL for appointment detail"""
        return f"/calendar/appointment/{self.id}/"


class BookingSettings(models.Model):
    """
    Global settings for the calendar booking system
    """

    calendar_user = models.OneToOneField(
        CalendarUser, on_delete=models.CASCADE, related_name="booking_settings"
    )

    # Booking window settings
    min_notice_hours = models.PositiveIntegerField(
        default=24, help_text="Minimum hours notice required for bookings"
    )
    max_bookings_per_day = models.PositiveIntegerField(
        default=10, help_text="Maximum appointments per day (0 = unlimited)"
    )

    # Email settings
    send_confirmation_emails = models.BooleanField(default=True)
    send_reminder_emails = models.BooleanField(default=True)
    reminder_hours_before = models.PositiveIntegerField(
        default=24, help_text="Hours before appointment to send reminder"
    )

    # Customization
    booking_page_title = models.CharField(
        max_length=200, blank=True, help_text="Custom title for booking page"
    )
    booking_page_description = models.TextField(
        blank=True, help_text="Description shown on booking page"
    )
    success_message = models.TextField(
        blank=True,
        default="Thank you for booking! You will receive a confirmation email shortly.",
        help_text="Message shown after successful booking",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Booking Settings"
        verbose_name_plural = "Booking Settings"

    def __str__(self):
        return f"Booking Settings - {self.calendar_user.user.username}"
