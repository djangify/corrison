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
    FIXED: Only send ONE email per appointment creation
    """
    if created:
        # New appointment created - send emails to owner and customer
        send_new_appointment_notification_to_owner(instance)

        # FIXED: Only send customer email based on final status
        if instance.status == "confirmed":
            # Send confirmed email directly (no need for pending email)
            send_appointment_confirmed_email(instance)
        else:
            # Only send pending email if actually pending
            send_new_appointment_confirmation_to_customer(instance)
    else:
        # Existing appointment updated - only send if status actually changed
        if instance.status == "confirmed" and instance.confirmed_at:
            # Only send if this is a status change from pending to confirmed
            send_appointment_confirmed_email(instance)
        elif instance.status == "cancelled" and instance.cancelled_at:
            send_appointment_cancelled_email(instance)


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
    site_url = getattr(settings, "SITE_URL", "https://corrisonapi.com")

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

To manage this appointment, visit your business dashboard:
{site_url}/calendar/my-appointments/

Customer Management Link (what the customer sees):
{site_url}/calendar/appointment?id={appointment.id}&email={appointment.customer_email}

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


def send_new_appointment_confirmation_to_customer(appointment):
    """
    Send initial confirmation email to customer when appointment is PENDING
    FIXED: Only called for truly pending appointments
    """
    calendar_user = appointment.calendar_user

    subject = f"Appointment Request Received - {appointment.appointment_type.name}"

    # Get the site URL
    site_url = getattr(settings, "SITE_URL", "https://corrisonapi.com")

    message = f"""
Dear {appointment.customer_name},

Thank you for your appointment request with {calendar_user.display_name}!

Your appointment request has been received and is pending confirmation.

Appointment Details:
- Service: {appointment.appointment_type.name}
- Date: {appointment.date.strftime("%B %d, %Y")}
- Time: {appointment.start_time.strftime("%I:%M %p")} - {appointment.end_time.strftime("%I:%M %p")}
- Provider: {calendar_user.display_name}

You will receive another email once your appointment is confirmed.

To view or cancel your appointment request, click here:
{site_url}/calendar/appointment?id={appointment.id}&email={appointment.customer_email}

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
        print(f"Failed to send customer confirmation email: {e}")


def send_appointment_confirmed_email(appointment):
    """
    Send email when appointment is confirmed
    FIXED: This is the MAIN customer email for confirmed appointments
    """
    calendar_user = appointment.calendar_user

    subject = f"Appointment Confirmed - {appointment.appointment_type.name}"

    # Get the site URL
    site_url = getattr(settings, "SITE_URL", "https://corrisonapi.com")

    message = f"""
Dear {appointment.customer_name},

Great news! Your appointment has been confirmed.

Appointment Details:
- Service: {appointment.appointment_type.name}
- Date: {appointment.date.strftime("%B %d, %Y")}
- Time: {appointment.start_time.strftime("%I:%M %p")} - {appointment.end_time.strftime("%I:%M %p")}
- Provider: {calendar_user.display_name}

{calendar_user.booking_instructions if calendar_user.booking_instructions else ""}

To view, edit, or cancel your appointment, click here:
{site_url}/calendar/appointment?id={appointment.id}&email={appointment.customer_email}

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
    site_url = getattr(settings, "SITE_URL", "https://corrisonapi.com")

    message = f"""
Dear {appointment.customer_name},

Your appointment has been cancelled.

Cancelled Appointment:
- Service: {appointment.appointment_type.name}
- Date: {appointment.date.strftime("%B %d, %Y")}
- Time: {appointment.start_time.strftime("%I:%M %p")} - {appointment.end_time.strftime("%I:%M %p")}

If you need to book a new appointment, please visit:
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


def send_appointment_updated_email(appointment):
    """
    Send email when appointment is updated (called manually when needed)
    """
    subject = f"Appointment Updated - {appointment.appointment_type.name}"

    # Get the site URL
    site_url = getattr(settings, "SITE_URL", "https://corrisonapi.com")

    message = f"""
Dear {appointment.customer_name},

Your appointment has been updated.

Updated Appointment Details:
- Service: {appointment.appointment_type.name}
- Date: {appointment.date.strftime("%B %d, %Y")}
- Time: {appointment.start_time.strftime("%I:%M %p")} - {appointment.end_time.strftime("%I:%M %p")}
- Provider: {appointment.calendar_user.display_name}

To view your appointment details, click here:
{site_url}/calendar/appointment?id={appointment.id}&email={appointment.customer_email}

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
        print(f"Failed to send update email: {e}")
