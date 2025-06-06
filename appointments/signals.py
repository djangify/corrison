# appointments/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from .models import Appointment, CalendarUser, BookingSettings

User = get_user_model()


@receiver(post_save, sender=User)
def create_calendar_user(sender, instance, created, **kwargs):
    """
    Automatically create a CalendarUser profile when a User is created
    """
    if created:
        calendar_user = CalendarUser.objects.create(
            user=instance,
            business_name=instance.get_full_name() or instance.username,
            is_calendar_active=False,  # Inactive by default until user configures it
        )

        # Create default booking settings
        BookingSettings.objects.create(
            calendar_user=calendar_user,
            booking_page_title=f"Book with {calendar_user.display_name}",
            booking_page_description="Select an appointment type and time that works for you.",
        )


@receiver(post_save, sender=Appointment)
def handle_appointment_status_change(sender, instance, created, **kwargs):
    """
    Handle appointment status changes - send emails, etc.
    """
    if created:
        # New appointment created
        send_appointment_confirmation_email(instance)
        send_new_appointment_notification_to_owner(instance)
    else:
        # Existing appointment updated
        if instance.status == "confirmed" and instance.confirmed_at:
            send_appointment_confirmed_email(instance)
        elif instance.status == "cancelled" and instance.cancelled_at:
            send_appointment_cancelled_email(instance)


def send_appointment_confirmation_email(appointment):
    """
    Send confirmation email to customer when appointment is booked
    """
    calendar_user = appointment.calendar_user
    booking_settings = getattr(calendar_user, "booking_settings", None)

    if not booking_settings or not booking_settings.send_confirmation_emails:
        return

    subject = f"Appointment Booked - {appointment.appointment_type.name}"

    # Get the site URL
    site_url = getattr(settings, "SITE_URL", "http://localhost:8000")

    message = f"""
Dear {appointment.customer_name},

Your appointment has been booked successfully!

Appointment Details:
- Service: {appointment.appointment_type.name}
- Date: {appointment.date.strftime("%B %d, %Y")}
- Time: {appointment.start_time.strftime("%I:%M %p")} - {appointment.end_time.strftime("%I:%M %p")}
- Duration: {appointment.duration_minutes} minutes
- Provider: {calendar_user.display_name}

Status: {appointment.get_status_display()}

{f"Amount: ${appointment.payment_amount}" if appointment.payment_required else ""}

{f"Notes: {appointment.customer_notes}" if appointment.customer_notes else ""}

To view or cancel your appointment, visit:
{site_url}/calendar/appointment/{appointment.id}/?email={appointment.customer_email}

Thank you for booking with us!

Best regards,
{calendar_user.display_name}
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[appointment.customer_email],
            fail_silently=True,
        )
    except Exception as e:
        # Log error but don't fail the appointment creation
        print(f"Failed to send confirmation email: {e}")


def send_new_appointment_notification_to_owner(appointment):
    """
    Send notification to calendar owner about new appointment
    """
    calendar_user = appointment.calendar_user
    owner_email = calendar_user.user.email

    if not owner_email:
        return

    subject = f"New Appointment Booked - {appointment.appointment_type.name}"

    # Get the site URL
    site_url = getattr(settings, "SITE_URL", "http://localhost:8000")

    message = f"""
You have a new appointment booking!

Appointment Details:
- Customer: {appointment.customer_name}
- Email: {appointment.customer_email}
- Phone: {appointment.customer_phone or "Not provided"}
- Service: {appointment.appointment_type.name}
- Date: {appointment.date.strftime("%B %d, %Y")}
- Time: {appointment.start_time.strftime("%I:%M %p")} - {appointment.end_time.strftime("%I:%M %p")}
- Status: {appointment.get_status_display()}

{f"Customer Notes: {appointment.customer_notes}" if appointment.customer_notes else ""}

{f"Payment Required: ${appointment.payment_amount}" if appointment.payment_required else ""}

To manage this appointment, visit your admin panel:
{site_url}/admin/appointments/appointment/{appointment.id}/change/

Best regards,
Your Calendar System
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[owner_email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send owner notification email: {e}")


def send_appointment_confirmed_email(appointment):
    """
    Send email when appointment is confirmed by owner
    """
    calendar_user = appointment.calendar_user
    booking_settings = getattr(calendar_user, "booking_settings", None)

    if not booking_settings or not booking_settings.send_confirmation_emails:
        return

    subject = f"Appointment Confirmed - {appointment.appointment_type.name}"

    # Get the site URL
    site_url = getattr(settings, "SITE_URL", "http://localhost:8000")

    message = f"""
Dear {appointment.customer_name},

Great news! Your appointment has been confirmed.

Appointment Details:
- Service: {appointment.appointment_type.name}
- Date: {appointment.date.strftime("%B %d, %Y")}
- Time: {appointment.start_time.strftime("%I:%M %p")} - {appointment.end_time.strftime("%I:%M %p")}
- Provider: {calendar_user.display_name}

{calendar_user.booking_instructions if calendar_user.booking_instructions else ""}

To view or cancel your appointment, visit:
{site_url}/calendar/appointment/{appointment.id}/?email={appointment.customer_email}

We look forward to seeing you!

Best regards,
{calendar_user.display_name}
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[appointment.customer_email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send confirmation email: {e}")


def send_appointment_cancelled_email(appointment):
    """
    Send email when appointment is cancelled
    """
    subject = f"Appointment Cancelled - {appointment.appointment_type.name}"

    # Get the site URL
    site_url = getattr(settings, "SITE_URL", "http://localhost:8000")

    message = f"""
Dear {appointment.customer_name},

Your appointment has been cancelled.

Cancelled Appointment:
- Service: {appointment.appointment_type.name}
- Date: {appointment.date.strftime("%B %d, %Y")}
- Time: {appointment.start_time.strftime("%I:%M %p")} - {appointment.end_time.strftime("%I:%M %p")}

If you need to reschedule, please visit our booking page:
{site_url}/calendar/

Thank you for your understanding.

Best regards,
{appointment.calendar_user.display_name}
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[appointment.customer_email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send cancellation email: {e}")
