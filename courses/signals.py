from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Enrollment, Course


@receiver(post_save, sender=Enrollment)
def handle_enrollment_created(sender, instance, created, **kwargs):
    """
    Handle new enrollments - send welcome email, update course stats
    """
    if created:
        # Send welcome email to student
        send_enrollment_welcome_email(instance)

        # Send notification to instructor
        send_instructor_enrollment_notification(instance)


@receiver(post_save, sender=Enrollment)
def handle_enrollment_completed(sender, instance, **kwargs):
    """
    Handle course completion - send congratulations email
    """
    if instance.status == "completed" and instance.completed_at:
        send_course_completion_email(instance)


def send_enrollment_welcome_email(enrollment):
    """
    Send welcome email to student when they enroll in a course
    """
    if not hasattr(settings, "DEFAULT_FROM_EMAIL"):
        return

    subject = f"Welcome to {enrollment.course.name}!"

    message = f"""
Dear {enrollment.user.get_full_name() or enrollment.user.username},

Welcome to "{enrollment.course.name}"!

You've successfully enrolled in this course taught by {enrollment.course.instructor.get_full_name() or enrollment.course.instructor.username}.

Course Details:
- Difficulty: {enrollment.course.get_difficulty_display()}
- Duration: {enrollment.course.estimated_duration}
- Lessons: {enrollment.course.lesson_count}

You can start learning right away by visiting your course dashboard.

Happy learning!

Best regards,
The {getattr(settings, "SITE_NAME", "Corrison")} Team
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"),
            recipient_list=[enrollment.user.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send enrollment welcome email: {e}")


def send_instructor_enrollment_notification(enrollment):
    """
    Notify instructor about new enrollment
    """
    if not hasattr(settings, "DEFAULT_FROM_EMAIL"):
        return

    instructor_email = enrollment.course.instructor.email
    if not instructor_email:
        return

    subject = f"New student enrolled in {enrollment.course.name}"

    message = f"""
Good news! You have a new student in your course.

Student: {enrollment.user.get_full_name() or enrollment.user.username}
Email: {enrollment.user.email}
Course: {enrollment.course.name}
Enrolled: {enrollment.created_at.strftime("%B %d, %Y at %I:%M %p")}

Your course now has {enrollment.course.total_enrollments} total enrollments.

You can view your course analytics in your instructor dashboard.

Best regards,
The {getattr(settings, "SITE_NAME", "Corrison")} Team
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"),
            recipient_list=[instructor_email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send instructor notification email: {e}")


def send_course_completion_email(enrollment):
    """
    Send congratulations email when student completes a course
    """
    if not hasattr(settings, "DEFAULT_FROM_EMAIL"):
        return

    subject = f"Congratulations! You completed {enrollment.course.name}"

    message = f"""
Congratulations {enrollment.user.get_full_name() or enrollment.user.username}!

You have successfully completed "{enrollment.course.name}" taught by {enrollment.course.instructor.get_full_name() or enrollment.course.instructor.username}.

Course Statistics:
- Started: {enrollment.created_at.strftime("%B %d, %Y")}
- Completed: {enrollment.completed_at.strftime("%B %d, %Y")}
- Total Lessons: {enrollment.course.lesson_count}
- Duration: {enrollment.course.estimated_duration}

We hope you found this course valuable and look forward to seeing you in more courses!

Keep learning!

Best regards,
The {getattr(settings, "SITE_NAME", "Corrison")} Team
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"),
            recipient_list=[enrollment.user.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send course completion email: {e}")


@receiver(post_save, sender=Course)
def handle_course_published(sender, instance, **kwargs):
    """
    Handle course publication - could send notifications to followers
    """
    # This is a placeholder for future functionality
    # Could notify users who follow this instructor, etc.
    pass
