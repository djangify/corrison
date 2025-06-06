# checkout/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Payment


@receiver(post_save, sender=Payment)
def handle_appointment_payment(sender, instance, created, **kwargs):
    """
    Handle appointment confirmation when payment is completed
    """
    if instance.status == "completed" and instance.order.is_appointment_order:
        # Get the associated appointment
        try:
            appointment = instance.order.appointment
            if appointment and appointment.status == "pending":
                # Confirm the appointment
                appointment.status = "confirmed"
                appointment.payment_status = "paid"
                appointment.confirmed_at = timezone.now()
                appointment.save()

                print(f"Appointment {appointment.id} confirmed after payment")

        except AttributeError:
            # No appointment associated with this order
            pass
