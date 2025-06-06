from django.contrib import admin
from django.db import models
from django.utils.html import format_html
from django.urls import reverse
from tinymce.widgets import TinyMCE
from .models import Category, Course, Lesson, Enrollment, CourseSettings


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = (
        "title",
        "youtube_url",
        "duration_minutes",
        "order",
        "is_preview",
        "is_published",
    )
    readonly_fields = ("created_at",)
    ordering = ("order",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "course_count_display", "color_display", "order")
    list_editable = ("order",)
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}

    fieldsets = (
        (None, {"fields": ("name", "slug", "description")}),
        ("Display", {"fields": ("color", "icon", "order")}),
    )

    def course_count_display(self, obj):
        count = obj.course_count
        url = reverse("admin:courses_course_changelist") + f"?category__id={obj.id}"
        return format_html('<a href="{}">{} courses</a>', url, count)

    course_count_display.short_description = "Courses"

    def color_display(self, obj):
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc;"></div>',
            obj.color,
        )

    color_display.short_description = "Color"


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "instructor",
        "category",
        "difficulty",
        "price_display",
        "lesson_count_display",
        "enrollment_count_display",
        "is_published",
        "created_at",
    )
    list_filter = ("is_published", "difficulty", "category", "instructor", "created_at")
    search_fields = ("name", "description", "instructor__username", "instructor__email")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("is_published",)
    inlines = [LessonInline]

    fieldsets = (
        (None, {"fields": ("name", "slug", "instructor", "category")}),
        (
            "Content",
            {
                "fields": (
                    "short_description",
                    "description",
                    "thumbnail",
                    "intro_video_url",
                )
            },
        ),
        (
            "Course Settings",
            {"fields": ("difficulty", "estimated_duration", "language", "price")},
        ),
        ("Access & Publishing", {"fields": ("requires_enrollment", "is_published")}),
        (
            "SEO",
            {
                "fields": ("meta_title", "meta_description", "meta_keywords"),
                "classes": ("collapse",),
            },
        ),
        ("Stats", {"fields": ("total_enrollments",), "classes": ("collapse",)}),
    )

    readonly_fields = ("created_at", "updated_at")

    formfield_overrides = {
        models.TextField: {"widget": TinyMCE(attrs={"cols": 80, "rows": 20})},
    }

    def price_display(self, obj):
        if obj.is_free:
            return format_html('<span style="color: green;">Free</span>')
        return f"${obj.price}"

    price_display.short_description = "Price"
    price_display.admin_order_field = "price"

    def lesson_count_display(self, obj):
        count = obj.lesson_count
        url = reverse("admin:courses_lesson_changelist") + f"?course__id={obj.id}"
        return format_html('<a href="{}">{} lessons</a>', url, count)

    lesson_count_display.short_description = "Lessons"

    def enrollment_count_display(self, obj):
        count = obj.total_enrollments
        url = reverse("admin:courses_enrollment_changelist") + f"?course__id={obj.id}"
        return format_html('<a href="{}">{} enrollments</a>', url, count)

    enrollment_count_display.short_description = "Enrollments"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("instructor", "category")
            .prefetch_related("lessons")
        )


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "course",
        "instructor_name",
        "order",
        "duration_display",
        "is_preview",
        "is_published",
        "video_status",
        "created_at",
    )
    list_filter = ("is_published", "is_preview", "course", "course__instructor")
    search_fields = (
        "title",
        "description",
        "course__name",
        "course__instructor__username",
    )
    list_editable = ("order", "is_preview", "is_published")

    fieldsets = (
        (None, {"fields": ("course", "title", "slug")}),
        (
            "Content",
            {"fields": ("description", "content", "youtube_url", "duration_minutes")},
        ),
        ("Settings", {"fields": ("order", "is_preview", "is_published")}),
    )

    readonly_fields = ("created_at", "updated_at")

    formfield_overrides = {
        models.TextField: {"widget": TinyMCE(attrs={"cols": 80, "rows": 15})},
    }

    def instructor_name(self, obj):
        return obj.course.instructor.username

    instructor_name.short_description = "Instructor"
    instructor_name.admin_order_field = "course__instructor__username"

    def duration_display(self, obj):
        if obj.duration_minutes:
            hours = obj.duration_minutes // 60
            minutes = obj.duration_minutes % 60
            if hours:
                return f"{hours}h {minutes}m"
            return f"{minutes}m"
        return "-"

    duration_display.short_description = "Duration"
    duration_display.admin_order_field = "duration_minutes"

    def video_status(self, obj):
        if obj.youtube_url:
            return format_html('<span style="color: green;">✓ YouTube</span>')
        return format_html('<span style="color: orange;">No Video</span>')

    video_status.short_description = "Video"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("course__instructor")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "course",
        "instructor_name",
        "status",
        "progress_display",
        "last_accessed",
        "created_at",
    )
    list_filter = ("status", "course", "course__instructor", "created_at")
    search_fields = (
        "user__username",
        "user__email",
        "course__name",
        "course__instructor__username",
    )
    readonly_fields = ("created_at", "updated_at", "progress_percentage")

    fieldsets = (
        (None, {"fields": ("user", "course", "status")}),
        (
            "Progress",
            {
                "fields": (
                    "progress_percentage",
                    "progress_data",
                    "last_accessed",
                    "completed_at",
                )
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    actions = ["mark_active", "mark_completed", "mark_paused"]

    def instructor_name(self, obj):
        return obj.course.instructor.username

    instructor_name.short_description = "Instructor"
    instructor_name.admin_order_field = "course__instructor__username"

    def progress_display(self, obj):
        percentage = obj.progress_percentage
        if percentage == 100:
            color = "green"
        elif percentage >= 50:
            color = "orange"
        else:
            color = "red"

        return format_html(
            '<div style="width: 100px; background: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background: {}; height: 20px; border-radius: 3px; text-align: center; line-height: 20px; color: white; font-size: 12px;">'
            "{}%"
            "</div></div>",
            percentage,
            color,
            int(percentage),
        )

    progress_display.short_description = "Progress"

    def mark_active(self, request, queryset):
        updated = queryset.update(status="active")
        self.message_user(request, f"{updated} enrollments marked as active.")

    mark_active.short_description = "Mark selected enrollments as active"

    def mark_completed(self, request, queryset):
        from django.utils import timezone

        updated = queryset.update(status="completed", completed_at=timezone.now())
        self.message_user(request, f"{updated} enrollments marked as completed.")

    mark_completed.short_description = "Mark selected enrollments as completed"

    def mark_paused(self, request, queryset):
        updated = queryset.update(status="paused")
        self.message_user(request, f"{updated} enrollments marked as paused.")

    mark_paused.short_description = "Mark selected enrollments as paused"

    def get_queryset(self, request):
        return (
            super().get_queryset(request).select_related("user", "course__instructor")
        )


@admin.register(CourseSettings)
class CourseSettingsAdmin(admin.ModelAdmin):
    """
    Admin for course page settings - singleton model
    """

    def has_add_permission(self, request):
        """Only allow adding if no instance exists"""
        return not CourseSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Don't allow deletion of settings"""
        return False

    def changelist_view(self, request, extra_context=None):
        """Redirect to the single instance edit page"""
        try:
            settings = CourseSettings.get_settings()
            return self.changeform_view(request, str(settings.pk))
        except Exception:
            return super().changelist_view(request, extra_context)

    fieldsets = (
        (
            "Page Content",
            {
                "fields": ("page_title", "page_subtitle", "page_description"),
                "description": "Main content for the courses page header",
            },
        ),
        (
            "External Course Links",
            {
                "fields": (
                    ("external_course_1_title", "external_course_1_url"),
                    ("external_course_2_title", "external_course_2_url"),
                    ("external_course_3_title", "external_course_3_url"),
                ),
                "description": "Links to external courses (e.g., paid courses on Udemy, Teachable, etc.)",
                "classes": ("collapse",),
            },
        ),
    )

    formfield_overrides = {
        models.TextField: {"widget": TinyMCE(attrs={"cols": 80, "rows": 10})},
    }
