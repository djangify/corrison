# Generated by Django 5.2.1 on 2025-06-03 08:56

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
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(blank=True, max_length=255, unique=True)),
                ('description', models.TextField(blank=True)),
                ('color', models.CharField(default='#3B82F6', help_text='Hex color for category display', max_length=7)),
                ('icon', models.CharField(blank=True, help_text='Icon class or name for category', max_length=50)),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Course Category',
                'verbose_name_plural': 'Course Categories',
                'ordering': ['order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(blank=True, max_length=255, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('meta_title', models.CharField(blank=True, max_length=255, null=True)),
                ('meta_description', models.TextField(blank=True, null=True)),
                ('meta_keywords', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.TextField()),
                ('short_description', models.CharField(help_text='Brief description for course cards', max_length=300)),
                ('difficulty', models.CharField(choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')], default='beginner', max_length=12)),
                ('estimated_duration', models.CharField(blank=True, help_text="e.g., '4 weeks', '2 hours', '10 lessons'", max_length=50)),
                ('language', models.CharField(default='English', max_length=50)),
                ('thumbnail', models.ImageField(blank=True, null=True, upload_to='courses/thumbnails/')),
                ('intro_video_url', models.URLField(blank=True, help_text='YouTube URL for course introduction video')),
                ('price', models.DecimalField(blank=True, decimal_places=2, help_text='Leave blank for free courses', max_digits=10, null=True)),
                ('is_published', models.BooleanField(default=False)),
                ('requires_enrollment', models.BooleanField(default=True, help_text='If false, anyone can view all lessons')),
                ('total_enrollments', models.PositiveIntegerField(default=0)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='courses', to='courses.category')),
                ('instructor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='courses_teaching', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Course',
                'verbose_name_plural': 'Courses',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Enrollment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('completed', 'Completed'), ('paused', 'Paused'), ('cancelled', 'Cancelled')], default='active', max_length=10)),
                ('progress_data', models.JSONField(default=dict, help_text='Stores completed lessons, progress percentages, etc.')),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('last_accessed', models.DateTimeField(blank=True, null=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='courses.course')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='course_enrollments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Enrollment',
                'verbose_name_plural': 'Enrollments',
            },
        ),
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('title', models.CharField(max_length=200)),
                ('slug', models.SlugField(blank=True, max_length=255)),
                ('description', models.TextField(blank=True)),
                ('youtube_url', models.URLField(blank=True, help_text='YouTube URL for this lesson')),
                ('duration_minutes', models.PositiveIntegerField(blank=True, help_text='Lesson duration in minutes', null=True)),
                ('content', models.TextField(blank=True, help_text='Additional text content, notes, resources')),
                ('order', models.PositiveIntegerField(default=0)),
                ('is_preview', models.BooleanField(default=False, help_text='Allow non-enrolled users to view this lesson')),
                ('is_published', models.BooleanField(default=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lessons', to='courses.course')),
            ],
            options={
                'verbose_name': 'Lesson',
                'verbose_name_plural': 'Lessons',
                'ordering': ['order', 'created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='course',
            index=models.Index(fields=['slug'], name='courses_cou_slug_2e551f_idx'),
        ),
        migrations.AddIndex(
            model_name='course',
            index=models.Index(fields=['is_published'], name='courses_cou_is_publ_4b99b9_idx'),
        ),
        migrations.AddIndex(
            model_name='course',
            index=models.Index(fields=['instructor'], name='courses_cou_instruc_d2e347_idx'),
        ),
        migrations.AddIndex(
            model_name='enrollment',
            index=models.Index(fields=['user'], name='courses_enr_user_id_6911bd_idx'),
        ),
        migrations.AddIndex(
            model_name='enrollment',
            index=models.Index(fields=['course'], name='courses_enr_course__a70609_idx'),
        ),
        migrations.AddIndex(
            model_name='enrollment',
            index=models.Index(fields=['status'], name='courses_enr_status_4fd017_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='enrollment',
            unique_together={('user', 'course')},
        ),
        migrations.AddIndex(
            model_name='lesson',
            index=models.Index(fields=['course', 'order'], name='courses_les_course__dc0bc6_idx'),
        ),
        migrations.AddIndex(
            model_name='lesson',
            index=models.Index(fields=['is_published'], name='courses_les_is_publ_ebf633_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='lesson',
            unique_together={('course', 'slug')},
        ),
    ]
