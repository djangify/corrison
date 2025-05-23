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
    settings = ContactPageSettings.objects.first()
    if not settings:
        settings = ContactPageSettings.objects.create()
    
    serializer = ContactPageSettingsSerializer(settings)
    return Response(serializer.data)