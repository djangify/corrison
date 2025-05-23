# core/views.py
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .serializers import ContactMessageSerializer
from .models import ContactPageSettings
from .serializers import ContactPageSettingsSerializer

def index(request):
    """
    Home/Index page view.
    """
    context = {
        'page_title': 'Corrison - Home',
        'breadcrumbs': [
            {'title': 'Home'}
        ]
    }

    return render(request, 'index.html', context)

@api_view(['POST'])
@permission_classes([AllowAny])
def submit_contact_message(request):
    serializer = ContactMessageSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "Thank you for contacting us. We'll get back to you soon!"},
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
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
                status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )