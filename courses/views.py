from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import Count, Q
from .models import Course, Lesson, Enrollment, Category
from .serializers import (
    CourseListSerializer,
    CourseDetailSerializer,
    LessonSerializer,
    EnrollmentSerializer,
    EnrollmentCreateSerializer,
    LessonProgressSerializer,
    CategorySerializer,
    CourseCreateUpdateSerializer,
    LessonCreateUpdateSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for course categories
    """

    queryset = Category.objects.annotate(
        published_course_count=Count("courses", filter=Q(courses__is_published=True))
    ).order_by("order", "name")
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for courses with different permissions for instructors vs students
    """

    permission_classes = [AllowAny]  # Custom permission handling in methods
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["category", "difficulty", "instructor"]
    search_fields = ["name", "description", "short_description", "instructor__username"]
    ordering_fields = ["created_at", "name", "total_enrollments", "price"]
    ordering = ["-created_at"]
    lookup_field = "slug"

    def get_queryset(self):
        """Filter queryset based on action and permissions"""
        if self.action in ["my_courses", "my_teaching"]:
            # These require authentication
            return Course.objects.none()

        # Public courses
        return (
            Course.objects.filter(is_published=True)
            .select_related("instructor", "category")
            .prefetch_related("lessons")
        )

    def get_serializer_class(self):
        """Use appropriate serializer based on action"""
        if self.action == "retrieve":
            return CourseDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return CourseCreateUpdateSerializer
        return CourseListSerializer

    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
            "my_teaching",
        ]:
            return [IsAuthenticated()]
        return [AllowAny()]

    def perform_create(self, serializer):
        """Set instructor to current user"""
        serializer.save(instructor=self.request.user)

    def perform_update(self, serializer):
        """Only allow instructor to update their own courses"""
        course = self.get_object()
        if course.instructor != self.request.user:
            raise PermissionError("You can only edit your own courses")
        serializer.save()

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def enroll(self, request, slug=None):
        """Enroll user in a course"""
        course = self.get_object()

        # Check if course is free or handle payment
        if not course.is_free:
            # TODO: Integrate with existing payment system
            return Response(
                {"error": "Paid courses require payment processing"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = EnrollmentCreateSerializer(
            data={"course_id": course.id}, context={"request": request}
        )

        if serializer.is_valid():
            enrollment = serializer.save()
            response_serializer = EnrollmentSerializer(enrollment)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def my_courses(self, request):
        """Get courses the user is enrolled in"""
        enrollments = (
            Enrollment.objects.filter(user=request.user)
            .select_related("course__instructor", "course__category")
            .order_by("-created_at")
        )

        serializer = EnrollmentSerializer(
            enrollments, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def my_teaching(self, request):
        """Get courses the user is teaching"""
        courses = (
            Course.objects.filter(instructor=request.user)
            .select_related("category")
            .prefetch_related("lessons")
        )

        serializer = CourseListSerializer(
            courses, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def lessons(self, request, slug=None):
        """Get lessons for a course"""
        course = self.get_object()
        lessons = course.lessons.filter(is_published=True).order_by("order")

        # Filter lessons based on access
        if request.user.is_authenticated:
            # Check if user is enrolled or if course doesn't require enrollment
            is_enrolled = Enrollment.objects.filter(
                user=request.user, course=course, status="active"
            ).exists()

            if not is_enrolled and course.requires_enrollment:
                # Only show preview lessons
                lessons = lessons.filter(is_preview=True)
        else:
            # Anonymous users only see preview lessons
            if course.requires_enrollment:
                lessons = lessons.filter(is_preview=True)

        serializer = LessonSerializer(lessons, many=True, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def stats(self, request, slug=None):
        """Get course statistics (public)"""
        course = self.get_object()

        stats = {
            "total_enrollments": course.total_enrollments,
            "lesson_count": course.lesson_count,
            "total_duration_minutes": course.total_duration_minutes,
            "difficulty": course.difficulty,
            "language": course.language,
        }

        return Response(stats)


class LessonViewSet(viewsets.ModelViewSet):
    """
    ViewSet for lessons
    """

    permission_classes = [AllowAny]  # Custom permission handling
    lookup_field = "slug"

    def get_queryset(self):
        """Filter lessons by course"""
        course_slug = self.kwargs.get("course_slug")
        if course_slug:
            return Lesson.objects.filter(
                course__slug=course_slug, course__is_published=True, is_published=True
            ).select_related("course")
        return Lesson.objects.none()

    def get_serializer_class(self):
        """Use appropriate serializer"""
        if self.action in ["create", "update", "partial_update"]:
            return LessonCreateUpdateSerializer
        return LessonSerializer

    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated()]
        return [AllowAny()]

    def retrieve(self, request, *args, **kwargs):
        """Custom retrieve to check access permissions"""
        lesson = self.get_object()

        # Check if user can access this lesson
        can_access = True

        if lesson.course.requires_enrollment and not lesson.is_preview:
            if not request.user.is_authenticated:
                can_access = False
            else:
                is_enrolled = Enrollment.objects.filter(
                    user=request.user, course=lesson.course, status="active"
                ).exists()
                can_access = is_enrolled

        if not can_access:
            return Response(
                {"error": "You need to be enrolled to access this lesson"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(lesson)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def complete(self, request, course_slug=None, slug=None):
        """Mark lesson as completed"""
        lesson = self.get_object()

        serializer = LessonProgressSerializer(
            data={"lesson_id": lesson.id}, context={"request": request}
        )

        if serializer.is_valid():
            enrollment = serializer.save()
            return Response(
                {
                    "message": "Lesson marked as completed",
                    "progress_percentage": enrollment.progress_percentage,
                }
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for user enrollments (read-only)
    """

    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return enrollments for current user"""
        return (
            Enrollment.objects.filter(user=self.request.user)
            .select_related("course__instructor", "course__category")
            .order_by("-created_at")
        )

    @action(detail=True, methods=["post"])
    def resume(self, request, pk=None):
        """Resume a paused enrollment"""
        enrollment = self.get_object()
        if enrollment.status == "paused":
            enrollment.status = "active"
            enrollment.save()
            serializer = self.get_serializer(enrollment)
            return Response(serializer.data)

        return Response(
            {"error": "Can only resume paused enrollments"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        """Pause an active enrollment"""
        enrollment = self.get_object()
        if enrollment.status == "active":
            enrollment.status = "paused"
            enrollment.save()
            serializer = self.get_serializer(enrollment)
            return Response(serializer.data)

        return Response(
            {"error": "Can only pause active enrollments"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["get"])
    def progress(self, request, pk=None):
        """Get detailed progress for an enrollment"""
        enrollment = self.get_object()

        lessons = enrollment.course.lessons.filter(is_published=True).order_by("order")
        progress_data = []

        for lesson in lessons:
            progress_data.append(
                {
                    "lesson_id": lesson.id,
                    "title": lesson.title,
                    "order": lesson.order,
                    "is_completed": enrollment.is_lesson_completed(lesson.id),
                    "duration_minutes": lesson.duration_minutes,
                }
            )

        return Response(
            {
                "enrollment_id": enrollment.id,
                "course": enrollment.course.name,
                "progress_percentage": enrollment.progress_percentage,
                "status": enrollment.status,
                "lessons": progress_data,
                "last_accessed": enrollment.last_accessed,
                "completed_at": enrollment.completed_at,
            }
        )
