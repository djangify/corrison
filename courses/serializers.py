from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Course, Lesson, Enrollment, Category

User = get_user_model()


class InstructorSerializer(serializers.ModelSerializer):
    """Basic instructor info"""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "full_name", "email"]

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class CategorySerializer(serializers.ModelSerializer):
    """Course category serializer"""

    course_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "color", "icon", "course_count"]

    def get_course_count(self, obj):
        # Use the annotated field if available, otherwise fall back to the property
        return getattr(obj, "published_course_count", obj.course_count)


class LessonSerializer(serializers.ModelSerializer):
    """Lesson serializer with video info"""

    youtube_embed_url = serializers.SerializerMethodField()
    youtube_thumbnail = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()
    can_access = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "content",
            "youtube_url",
            "youtube_embed_url",
            "youtube_thumbnail",
            "duration_minutes",
            "order",
            "is_preview",
            "is_completed",
            "can_access",
            "created_at",
        ]

    def get_youtube_embed_url(self, obj):
        return obj.get_youtube_embed_url()

    def get_youtube_thumbnail(self, obj):
        return obj.get_youtube_thumbnail()

    def get_is_completed(self, obj):
        """Check if current user completed this lesson"""
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False

        try:
            enrollment = Enrollment.objects.get(user=request.user, course=obj.course)
            return enrollment.is_lesson_completed(obj.id)
        except Enrollment.DoesNotExist:
            return False

    def get_can_access(self, obj):
        """Check if current user can access this lesson"""
        request = self.context.get("request")

        # Preview lessons are always accessible
        if obj.is_preview:
            return True

        # Course doesn't require enrollment
        if not obj.course.requires_enrollment:
            return True

        # Check if user is enrolled
        if request and request.user.is_authenticated:
            return Enrollment.objects.filter(
                user=request.user, course=obj.course, status="active"
            ).exists()

        return False


class CourseListSerializer(serializers.ModelSerializer):
    """Lightweight course serializer for listing"""

    instructor = InstructorSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    is_free = serializers.BooleanField(read_only=True)
    lesson_count = serializers.IntegerField(read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "name",
            "slug",
            "short_description",
            "thumbnail",
            "instructor",
            "category",
            "difficulty",
            "estimated_duration",
            "price",
            "is_free",
            "lesson_count",
            "total_enrollments",
            "is_enrolled",
            "progress_percentage",
            "created_at",
        ]

    def get_is_enrolled(self, obj):
        """Check if current user is enrolled"""
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False

        return Enrollment.objects.filter(
            user=request.user, course=obj, status="active"
        ).exists()

    def get_progress_percentage(self, obj):
        """Get user's progress in this course"""
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return 0

        try:
            enrollment = Enrollment.objects.get(
                user=request.user, course=obj, status="active"
            )
            return enrollment.progress_percentage
        except Enrollment.DoesNotExist:
            return 0


class CourseDetailSerializer(serializers.ModelSerializer):
    """Full course details with lessons"""

    instructor = InstructorSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    lessons = LessonSerializer(many=True, read_only=True)
    is_free = serializers.BooleanField(read_only=True)
    lesson_count = serializers.IntegerField(read_only=True)
    intro_video_embed_url = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    next_lesson = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "short_description",
            "instructor",
            "category",
            "difficulty",
            "estimated_duration",
            "language",
            "thumbnail",
            "intro_video_url",
            "intro_video_embed_url",
            "price",
            "is_free",
            "requires_enrollment",
            "lesson_count",
            "total_enrollments",
            "total_duration_minutes",
            "lessons",
            "is_enrolled",
            "progress_percentage",
            "next_lesson",
            "created_at",
            "updated_at",
        ]

    def get_intro_video_embed_url(self, obj):
        return obj.get_intro_video_embed_url()

    def get_is_enrolled(self, obj):
        """Check if current user is enrolled"""
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False

        return Enrollment.objects.filter(
            user=request.user, course=obj, status="active"
        ).exists()

    def get_progress_percentage(self, obj):
        """Get user's progress in this course"""
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return 0

        try:
            enrollment = Enrollment.objects.get(
                user=request.user, course=obj, status="active"
            )
            return enrollment.progress_percentage
        except Enrollment.DoesNotExist:
            return 0

    def get_next_lesson(self, obj):
        """Get the next lesson the user should watch"""
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None

        try:
            enrollment = Enrollment.objects.get(
                user=request.user, course=obj, status="active"
            )

            # Find first incomplete lesson
            for lesson in obj.lessons.filter(is_published=True).order_by("order"):
                if not enrollment.is_lesson_completed(lesson.id):
                    return {
                        "id": lesson.id,
                        "title": lesson.title,
                        "slug": lesson.slug,
                        "order": lesson.order,
                    }

            return None  # All lessons completed
        except Enrollment.DoesNotExist:
            return None


class EnrollmentSerializer(serializers.ModelSerializer):
    """Enrollment serializer"""

    course = CourseListSerializer(read_only=True)
    progress_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "course",
            "status",
            "progress_percentage",
            "last_accessed",
            "completed_at",
            "created_at",
        ]


class EnrollmentCreateSerializer(serializers.Serializer):
    """Serializer for creating enrollments"""

    course_id = serializers.IntegerField()

    def validate_course_id(self, value):
        """Validate course exists and is published"""
        try:
            course = Course.objects.get(id=value, is_published=True)
            self.course = course
            return value
        except Course.DoesNotExist:
            raise serializers.ValidationError("Course not found or not published")

    def validate(self, data):
        """Check if user can enroll"""
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required")

        # Check if already enrolled
        if Enrollment.objects.filter(user=request.user, course=self.course).exists():
            raise serializers.ValidationError("Already enrolled in this course")

        return data

    def create(self, validated_data):
        """Create enrollment"""
        request = self.context.get("request")
        enrollment = Enrollment.objects.create(user=request.user, course=self.course)

        # Update course enrollment count
        self.course.total_enrollments += 1
        self.course.save(update_fields=["total_enrollments"])

        return enrollment


class LessonProgressSerializer(serializers.Serializer):
    """Serializer for marking lesson progress"""

    lesson_id = serializers.IntegerField()
    completed = serializers.BooleanField(default=True)

    def validate_lesson_id(self, value):
        """Validate lesson exists"""
        try:
            lesson = Lesson.objects.get(id=value, is_published=True)
            self.lesson = lesson
            return value
        except Lesson.DoesNotExist:
            raise serializers.ValidationError("Lesson not found")

    def validate(self, data):
        """Check if user can access lesson"""
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required")

        # Check if user is enrolled in the course
        try:
            self.enrollment = Enrollment.objects.get(
                user=request.user, course=self.lesson.course, status="active"
            )
        except Enrollment.DoesNotExist:
            raise serializers.ValidationError("Not enrolled in this course")

        return data

    def save(self):
        """Mark lesson as completed"""
        if self.validated_data["completed"]:
            self.enrollment.mark_lesson_complete(self.lesson.id)
        return self.enrollment


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating courses (instructor use)"""

    class Meta:
        model = Course
        fields = [
            "name",
            "description",
            "short_description",
            "category",
            "difficulty",
            "estimated_duration",
            "language",
            "thumbnail",
            "intro_video_url",
            "price",
            "requires_enrollment",
            "is_published",
        ]

    def create(self, validated_data):
        """Create course with current user as instructor"""
        request = self.context.get("request")
        validated_data["instructor"] = request.user
        return super().create(validated_data)


class LessonCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating lessons (instructor use)"""

    class Meta:
        model = Lesson
        fields = [
            "title",
            "description",
            "content",
            "youtube_url",
            "duration_minutes",
            "order",
            "is_preview",
            "is_published",
        ]
