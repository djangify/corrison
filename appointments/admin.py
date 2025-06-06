# appointments/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    CalendarUser,
    AppointmentType,
    Availability,
    Appointment,
    BookingSettings,
)


@admin.register(CalendarUser)
class CalendarUserAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "business_name",
        "timezone",
        "is_calendar_active",
        "booking_window_days",
        "appointment_count",
        "created_at",
    )
    list_filter = ("is_calendar_active", "timezone", "created_at")
    search_fields = ("user__username", "user__email", "business_name")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("user", "business_name", "is_calendar_active")}),
        (
            "Settings",
            {
                "fields": (
                    "timezone",
                    "booking_window_days",
                    "buffer_minutes",
                    "booking_instructions",
                )
            },
        ),
        (
            "Weekly Availability",
            {
                "fields": (
                    ("monday_enabled", "monday_start", "monday_end"),
                    ("tuesday_enabled", "tuesday_start", "tuesday_end"),
                    ("wednesday_enabled", "wednesday_start", "wednesday_end"),
                    ("thursday_enabled", "thursday_start", "thursday_end"),
                    ("friday_enabled", "friday_start", "friday_end"),
                    ("saturday_enabled", "saturday_start", "saturday_end"),
                    ("sunday_enabled", "sunday_start", "sunday_end"),
                ),
                "description": "Set your default weekly schedule. Use Availability Overrides to modify specific dates.",
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def appointment_count(self, obj):
        """Count of appointments for this calendar user"""
        count = Appointment.objects.filter(appointment_type__calendar_user=obj).count()
        return f"{count} appointments"

    appointment_count.short_description = "Appointments"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")


class AppointmentInline(admin.TabularInline):
    model = Appointment
    extra = 0
    readonly_fields = ("created_at", "confirmed_at")
    fields = (
        "customer_name",
        "customer_email",
        "date",
        "start_time",
        "status",
        "payment_status",
        "created_at",
    )


@admin.register(AppointmentType)
class AppointmentTypeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "calendar_user",
        "duration_minutes",
        "price_display",
        "is_active",
        "appointment_count",
        "order",
    )
    list_filter = ("is_active", "requires_payment", "calendar_user")
    search_fields = ("name", "description", "calendar_user__user__username")
    list_editable = ("order", "is_active")
    readonly_fields = ("created_at", "updated_at")
    inlines = [AppointmentInline]

    fieldsets = (
        (None, {"fields": ("calendar_user", "name", "description", "order")}),
        (
            "Appointment Details",
            {
                "fields": (
                    "duration_minutes",
                    "price",
                    "requires_payment",
                    "color",
                    "is_active",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def price_display(self, obj):
        """Display price with formatting"""
        if obj.price:
            return f"${obj.price}"
        return "Free"

    price_display.short_description = "Price"
    price_display.admin_order_field = "price"

    def appointment_count(self, obj):
        """Count of appointments for this type"""
        count = obj.appointments.count()
        url = (
            reverse("admin:appointments_appointment_changelist")
            + f"?appointment_type__id={obj.id}"
        )
        return format_html('<a href="{}">{} bookings</a>', url, count)

    appointment_count.short_description = "Bookings"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("calendar_user__user")


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = (
        "calendar_user",
        "date",
        "start_time",
        "end_time",
        "is_available",
        "recurring_pattern",
        "recurring_until",
    )
    list_filter = (
        "is_available",
        "recurring_pattern",
        "date",
        "calendar_user",
    )
    search_fields = ("calendar_user__user__username", "notes")
    date_hierarchy = "date"

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "calendar_user",
                    "date",
                    "start_time",
                    "end_time",
                    "is_available",
                )
            },
        ),
        (
            "Recurring Pattern",
            {
                "fields": ("recurring_pattern", "recurring_until"),
                "classes": ("collapse",),
            },
        ),
        (
            "Notes",
            {
                "fields": ("notes",),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("calendar_user__user")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "customer_name",
        "appointment_type",
        "calendar_owner",
        "date",
        "start_time",
        "status",
        "payment_status_display",
        "created_at",
    )
    list_filter = (
        "status",
        "payment_status",
        "date",
        "appointment_type__calendar_user",
        "created_at",
    )
    search_fields = (
        "customer_name",
        "customer_email",
        "appointment_type__name",
        "appointment_type__calendar_user__user__username",
    )
    date_hierarchy = "date"
    readonly_fields = ("created_at", "updated_at", "confirmed_at", "cancelled_at")

    fieldsets = (
        (
            "Appointment Details",
            {
                "fields": (
                    "appointment_type",
                    "date",
                    "start_time",
                    "end_time",
                    "status",
                )
            },
        ),
        (
            "Customer Information",
            {
                "fields": (
                    "customer_name",
                    "customer_email",
                    "customer_phone",
                    "customer_notes",
                )
            },
        ),
        (
            "Payment Information",
            {
                "fields": (
                    "payment_required",
                    "payment_status",
                    "payment_amount",
                    "stripe_payment_intent_id",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Notes & Administration",
            {
                "fields": ("admin_notes",),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                    "confirmed_at",
                    "cancelled_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def calendar_owner(self, obj):
        """Display calendar owner username"""
        return obj.appointment_type.calendar_user.user.username

    calendar_owner.short_description = "Calendar Owner"
    calendar_owner.admin_order_field = "appointment_type__calendar_user__user__username"

    def payment_status_display(self, obj):
        """Display payment status with color coding"""
        colors = {
            "not_required": "gray",
            "pending": "orange",
            "paid": "green",
            "refunded": "red",
        }
        color = colors.get(obj.payment_status, "black")
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_payment_status_display(),
        )

    payment_status_display.short_description = "Payment"
    payment_status_display.admin_order_field = "payment_status"

    actions = ["mark_confirmed", "mark_cancelled", "mark_completed"]

    def mark_confirmed(self, request, queryset):
        """Bulk action to confirm appointments"""
        updated = queryset.filter(status="pending").update(
            status="confirmed", confirmed_at=timezone.now()
        )
        self.message_user(request, f"{updated} appointments marked as confirmed.")

    mark_confirmed.short_description = "Mark selected appointments as confirmed"

    def mark_cancelled(self, request, queryset):
        """Bulk action to cancel appointments"""
        updated = queryset.exclude(status="cancelled").update(
            status="cancelled", cancelled_at=timezone.now()
        )
        self.message_user(request, f"{updated} appointments marked as cancelled.")

    mark_cancelled.short_description = "Mark selected appointments as cancelled"

    def mark_completed(self, request, queryset):
        """Bulk action to mark appointments as completed"""
        updated = queryset.filter(status="confirmed").update(status="completed")
        self.message_user(request, f"{updated} appointments marked as completed.")

    mark_completed.short_description = "Mark selected appointments as completed"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("appointment_type__calendar_user__user")
        )


@admin.register(BookingSettings)
class BookingSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "calendar_user",
        "min_notice_hours",
        "max_bookings_per_day",
        "send_confirmation_emails",
        "send_reminder_emails",
    )
    list_filter = ("send_confirmation_emails", "send_reminder_emails")
    search_fields = ("calendar_user__user__username", "booking_page_title")

    fieldsets = (
        ("Calendar User", {"fields": ("calendar_user",)}),
        (
            "Booking Rules",
            {
                "fields": (
                    "min_notice_hours",
                    "max_bookings_per_day",
                )
            },
        ),
        (
            "Email Notifications",
            {
                "fields": (
                    "send_confirmation_emails",
                    "send_reminder_emails",
                    "reminder_hours_before",
                )
            },
        ),
        (
            "Page Customization",
            {
                "fields": (
                    "booking_page_title",
                    "booking_page_description",
                    "success_message",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("calendar_user__user")
