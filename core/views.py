# core/views.py
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import JsonResponse
from .models import SiteSettings, ContactMessage, ContactPageSettings
from .serializers import (
    SiteSettingsSerializer,
    ContactMessageSerializer,
    ContactPageSettingsSerializer,
)


def index(request):
    """
    Home/Index page view.
    """
    context = {"page_title": "Corrison - Home", "breadcrumbs": [{"title": "Home"}]}

    return render(request, "index.html", context)


@api_view(["POST"])
@permission_classes([AllowAny])
def submit_contact_message(request):
    serializer = ContactMessageSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "Thank you for contacting us. We'll get back to you soon!"},
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_contact_page_settings(request):
    try:
        settings = ContactPageSettings.objects.first()
        if settings:
            serializer = ContactPageSettingsSerializer(settings)
            return Response(serializer.data)
        else:
            return Response(
                {"error": "Contact settings not configured"},
                status=status.HTTP_404_NOT_FOUND,
            )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# NEW SITESETTINGS FUNCTIONALITY BELOW


@api_view(["GET"])
@permission_classes([AllowAny])
def site_settings(request):
    """
    Get site-wide settings for the frontend
    """
    try:
        settings = SiteSettings.get_settings()
        serializer = SiteSettingsSerializer(settings, context={"request": request})
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {"error": f"Unable to fetch site settings: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def contact_page_settings(request):
    """
    Get contact page settings (alternative endpoint name for consistency)
    """
    return get_contact_page_settings(request)


@api_view(["POST"])
@permission_classes([AllowAny])
def newsletter_signup(request):
    """
    Newsletter signup endpoint - placeholder for now
    You can implement this with your preferred email service
    """
    email = request.data.get("email")

    if not email:
        return Response(
            {"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    # TODO: Implement newsletter signup logic here
    # For now, just return success
    return Response(
        {"message": "Thank you for subscribing to our newsletter!"},
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Simple health check endpoint
    """
    return JsonResponse({"status": "healthy", "message": "Corrison API is running"})
