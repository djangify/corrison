from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import slugify
from core.models import TimestampedModel, SluggedModel, PublishableModel, SEOModel
import re

User = get_user_model()


class Category(SluggedModel, TimestampedModel):
    """Course categories"""

    description = models.TextField(blank=True)
    color = models.CharField(
        max_length=7, default="#3B82F6", help_text="Hex color for category display"
    )
    icon = models.CharField(
        max_length=50, blank=True, help_text="Icon class or name for category"
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Course Category"
        verbose_name_plural = "Course Categories"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    @property
    def course_count(self):
        """Get number of published courses in this category"""
        return self.courses.filter(is_published=True).count()


class CourseManager(models.Manager):
    """Custom manager for Course model"""

    def published(self):
        """Returns published courses"""
        return self.filter(is_published=True)

    def by_instructor(self, user):
        """Returns courses by specific instructor"""
        return self.filter(instructor=user)


class Course(SluggedModel, TimestampedModel, PublishableModel, SEOModel):
    """Course model - integrates with existing product system"""

    DIFFICULTY_CHOICES = [
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    ]

    # Basic Info
    instructor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="courses_teaching"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses",
    )
    description = models.TextField()
    short_description = models.CharField(
        max_length=300, help_text="Brief description for course cards"
    )

    # Course Details
    difficulty = models.CharField(
        max_length=12, choices=DIFFICULTY_CHOICES, default="beginner"
    )
    estimated_duration = models.CharField(
        max_length=50, blank=True, help_text="e.g., '4 weeks', '2 hours', '10 lessons'"
    )
    language = models.CharField(max_length=50, default="English")

    # Media
    thumbnail = models.ImageField(
        upload_to="courses/thumbnails/", blank=True, null=True
    )
    intro_video_url = models.URLField(
        blank=True, help_text="YouTube URL for course introduction video"
    )

    # Pricing (integrates with products)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Leave blank for free courses",
    )

    # Publishing & Access
    is_published = models.BooleanField(default=False)
    requires_enrollment = models.BooleanField(
        default=True, help_text="If false, anyone can view all lessons"
    )

    # Stats (calculated fields)
    total_enrollments = models.PositiveIntegerField(default=0)

    objects = CourseManager()

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_published"]),
            models.Index(fields=["instructor"]),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("courses:course_detail", kwargs={"slug": self.slug})

    @property
    def is_free(self):
        """Check if course is free"""
        return self.price is None or self.price == 0

    @property
    def lesson_count(self):
        """Get total number of lessons"""
        return self.lessons.filter(is_published=True).count()

    @property
    def total_duration_minutes(self):
        """Calculate total course duration"""
        return sum(lesson.duration_minutes or 0 for lesson in self.lessons.all())

    def get_intro_video_embed_url(self):
        """Convert YouTube URL to embed URL"""
        if not self.intro_video_url:
            return None
        return self._youtube_url_to_embed(self.intro_video_url)

    def _youtube_url_to_embed(self, url):
        """Helper to convert YouTube URL to embed format"""
        if "youtu.be" in url:
            video_id = url.split("/")[-1].split("?")[0]
        elif "youtube.com" in url:
            video_id = re.search(r"v=([^&]+)", url)
            video_id = video_id.group(1) if video_id else None
        else:
            return None

        return f"https://www.youtube.com/embed/{video_id}" if video_id else None


class Lesson(TimestampedModel, PublishableModel):
    """Individual lesson within a course"""

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    # Video
    youtube_url = models.URLField(blank=True, help_text="YouTube URL for this lesson")
    duration_minutes = models.PositiveIntegerField(
        null=True, blank=True, help_text="Lesson duration in minutes"
    )

    # Content
    content = models.TextField(
        blank=True, help_text="Additional text content, notes, resources"
    )

    # Ordering & Access
    order = models.PositiveIntegerField(default=0)
    is_preview = models.BooleanField(
        default=False, help_text="Allow non-enrolled users to view this lesson"
    )
    is_published = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Lesson"
        verbose_name_plural = "Lessons"
        ordering = ["order", "created_at"]
        unique_together = [["course", "slug"]]
        indexes = [
            models.Index(fields=["course", "order"]),
            models.Index(fields=["is_published"]),
        ]

    def __str__(self):
        return f"{self.course.name} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while (
                Lesson.objects.filter(course=self.course, slug=slug)
                .exclude(pk=self.pk)
                .exists()
            ):
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            "courses:lesson_detail",
            kwargs={"course_slug": self.course.slug, "lesson_slug": self.slug},
        )

    def get_youtube_embed_url(self):
        """Convert YouTube URL to embed URL"""
        if not self.youtube_url:
            return None
        return self.course._youtube_url_to_embed(self.youtube_url)

    def get_youtube_thumbnail(self):
        """Get YouTube thumbnail URL"""
        if not self.youtube_url:
            return None

        if "youtu.be" in self.youtube_url:
            video_id = self.youtube_url.split("/")[-1].split("?")[0]
        elif "youtube.com" in self.youtube_url:
            video_id = re.search(r"v=([^&]+)", self.youtube_url)
            video_id = video_id.group(1) if video_id else None
        else:
            return None

        return (
            f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            if video_id
            else None
        )


class Enrollment(TimestampedModel):
    """User enrollment in a course"""

    STATUS_CHOICES = [
        ("active", "Active"),
        ("completed", "Completed"),
        ("paused", "Paused"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="course_enrollments"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="enrollments"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")

    # Progress tracking
    progress_data = models.JSONField(
        default=dict, help_text="Stores completed lessons, progress percentages, etc."
    )

    # Completion tracking
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Enrollment"
        verbose_name_plural = "Enrollments"
        unique_together = [["user", "course"]]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["course"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.user.username} enrolled in {self.course.name}"

    @property
    def progress_percentage(self):
        """Calculate completion percentage"""
        total_lessons = self.course.lesson_count
        if total_lessons == 0:
            return 0

        completed_lessons = len(self.progress_data.get("completed_lessons", []))
        return min(100, (completed_lessons / total_lessons) * 100)

    def mark_lesson_complete(self, lesson_id):
        """Mark a lesson as completed"""
        completed_lessons = set(self.progress_data.get("completed_lessons", []))
        completed_lessons.add(lesson_id)
        self.progress_data["completed_lessons"] = list(completed_lessons)

        # Update timestamps
        from django.utils import timezone

        self.progress_data["last_lesson_completed_at"] = timezone.now().isoformat()
        self.last_accessed = timezone.now()

        # Check if course is complete
        if self.progress_percentage >= 100:
            self.status = "completed"
            self.completed_at = timezone.now()

        self.save()

    def is_lesson_completed(self, lesson_id):
        """Check if a lesson is completed"""
        return lesson_id in self.progress_data.get("completed_lessons", [])
