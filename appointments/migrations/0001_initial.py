# Generated by Django 5.2.1 on 2025-06-03 08:10

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AppointmentType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('duration_minutes', models.PositiveIntegerField()),
                ('price', models.DecimalField(blank=True, decimal_places=2, help_text='Leave blank for free appointments', max_digits=10, null=True)),
                ('color', models.CharField(default='#3B82F6', help_text='Hex color for calendar display', max_length=7)),
                ('is_active', models.BooleanField(default=True)),
                ('requires_payment', models.BooleanField(default=False, help_text='Whether payment is required before booking confirmation')),
                ('order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Appointment Type',
                'verbose_name_plural': 'Appointment Types',
                'ordering': ['order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_name', models.CharField(max_length=200)),
                ('customer_email', models.EmailField(max_length=254)),
                ('customer_phone', models.CharField(blank=True, max_length=20)),
                ('date', models.DateField()),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('status', models.CharField(choices=[('pending', 'Pending Confirmation'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled'), ('completed', 'Completed'), ('no_show', 'No Show')], default='pending', max_length=20)),
                ('customer_notes', models.TextField(blank=True, help_text='Notes from customer during booking')),
                ('admin_notes', models.TextField(blank=True, help_text='Internal notes for calendar owner')),
                ('payment_required', models.BooleanField(default=False)),
                ('payment_status', models.CharField(choices=[('not_required', 'Not Required'), ('pending', 'Payment Pending'), ('paid', 'Paid'), ('refunded', 'Refunded')], default='not_required', max_length=20)),
                ('payment_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('stripe_payment_intent_id', models.CharField(blank=True, max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('confirmed_at', models.DateTimeField(blank=True, null=True)),
                ('cancelled_at', models.DateTimeField(blank=True, null=True)),
                ('appointment_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to='appointments.appointmenttype')),
            ],
            options={
                'verbose_name': 'Appointment',
                'verbose_name_plural': 'Appointments',
                'ordering': ['date', 'start_time'],
            },
        ),
        migrations.CreateModel(
            name='CalendarUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('business_name', models.CharField(blank=True, max_length=200)),
                ('timezone', models.CharField(default='UTC', help_text="Timezone for this user's calendar (e.g., 'America/New_York')", max_length=50)),
                ('booking_window_days', models.PositiveIntegerField(default=30, help_text='How many days in advance customers can book')),
                ('buffer_minutes', models.PositiveIntegerField(default=15, help_text='Buffer time between appointments in minutes')),
                ('is_calendar_active', models.BooleanField(default=True, help_text="Whether this user's calendar is accepting bookings")),
                ('booking_instructions', models.TextField(blank=True, help_text='Instructions shown to customers when booking')),
                ('default_availability', models.JSONField(default=dict, help_text='Default weekly availability pattern')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='calendar_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Calendar User',
                'verbose_name_plural': 'Calendar Users',
            },
        ),
        migrations.CreateModel(
            name='BookingSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('min_notice_hours', models.PositiveIntegerField(default=24, help_text='Minimum hours notice required for bookings')),
                ('max_bookings_per_day', models.PositiveIntegerField(default=10, help_text='Maximum appointments per day (0 = unlimited)')),
                ('send_confirmation_emails', models.BooleanField(default=True)),
                ('send_reminder_emails', models.BooleanField(default=True)),
                ('reminder_hours_before', models.PositiveIntegerField(default=24, help_text='Hours before appointment to send reminder')),
                ('booking_page_title', models.CharField(blank=True, help_text='Custom title for booking page', max_length=200)),
                ('booking_page_description', models.TextField(blank=True, help_text='Description shown on booking page')),
                ('success_message', models.TextField(blank=True, default='Thank you for booking! You will receive a confirmation email shortly.', help_text='Message shown after successful booking')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('calendar_user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='booking_settings', to='appointments.calendaruser')),
            ],
            options={
                'verbose_name': 'Booking Settings',
                'verbose_name_plural': 'Booking Settings',
            },
        ),
        migrations.AddField(
            model_name='appointmenttype',
            name='calendar_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointment_types', to='appointments.calendaruser'),
        ),
        migrations.CreateModel(
            name='Availability',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('is_available', models.BooleanField(default=True, help_text='False = blocked time, True = available time')),
                ('recurring_pattern', models.CharField(choices=[('none', 'One-time only'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], default='none', max_length=10)),
                ('recurring_until', models.DateField(blank=True, help_text='When recurring pattern ends (leave blank for indefinite)', null=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('calendar_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='availability_slots', to='appointments.calendaruser')),
            ],
            options={
                'verbose_name': 'Availability',
                'verbose_name_plural': 'Availability Slots',
                'ordering': ['date', 'start_time'],
                'unique_together': {('calendar_user', 'date', 'start_time', 'end_time')},
            },
        ),
    ]
