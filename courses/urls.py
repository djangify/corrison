from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create main router
router = DefaultRouter()
router.register(r"categories", views.CategoryViewSet, basename="category")
router.register(r"courses", views.CourseViewSet, basename="course")
router.register(r"enrollments", views.EnrollmentViewSet, basename="enrollment")

app_name = "courses"

urlpatterns = [
    # Include the main router URLs
    path("", include(router.urls)),
    # Manual nested URLs for lessons within courses
    path(
        "courses/<str:course_slug>/lessons/",
        views.LessonViewSet.as_view({"get": "list", "post": "create"}),
        name="course-lessons-list",
    ),
    path(
        "courses/<str:course_slug>/lessons/<str:slug>/",
        views.LessonViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="course-lessons-detail",
    ),
    path(
        "courses/<str:course_slug>/lessons/<str:slug>/complete/",
        views.LessonViewSet.as_view({"post": "complete"}),
        name="course-lessons-complete",
    ),
]
