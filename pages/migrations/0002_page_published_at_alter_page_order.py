# Generated by Django 5.2 on 2025-05-07 13:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='published_at',
            field=models.DateTimeField(blank=True, help_text='Date/time when this page goes live', null=True),
        ),
        migrations.AlterField(
            model_name='page',
            name='order',
            field=models.PositiveIntegerField(default=0, help_text='Lower numbers appear first'),
        ),
    ]
