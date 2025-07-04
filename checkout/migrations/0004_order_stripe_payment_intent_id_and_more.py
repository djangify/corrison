# Generated by Django 5.2.1 on 2025-06-19 10:07

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0004_appointmentsettings_calendarsettings'),
        ('checkout', '0003_ordersettings'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='stripe_payment_intent_id',
            field=models.CharField(blank=True, db_index=True, help_text='Stripe Payment Intent ID for this order', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='download_token',
            field=models.CharField(blank=True, db_index=True, max_length=64, unique=True),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='max_downloads',
            field=models.PositiveIntegerField(blank=True, help_text='Maximum number of downloads allowed. None or 0 = unlimited', null=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='transaction_id',
            field=models.CharField(db_index=True, max_length=255, unique=True),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['stripe_payment_intent_id'], name='checkout_or_stripe__ef76db_idx'),
        ),
    ]
