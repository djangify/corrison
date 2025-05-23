# Create core/serializers.py
from rest_framework import serializers
from .models import ContactMessage
from .models import ContactPageSettings

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']

class ContactPageSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactPageSettings
        fields = '__all__'