from rest_framework import serializers
from .models import OrderSettings


class OrderSettingsSerializer(serializers.ModelSerializer):
    """Serializer for order page settings"""

    class Meta:
        model = OrderSettings
        fields = [
            "page_title",
            "page_subtitle",
            "page_description",
        ]
