# pages/serializers.py
from rest_framework import serializers
from .models import Page

class PageSerializer(serializers.ModelSerializer):
    hero_image = serializers.ImageField(read_only=True)

    class Meta:
        model = Page
        fields = [
            'id',
            'slug',
            'title',
            'subtitle',
            'hero_image',
            'content',
            'meta_description',
            'is_published',
            'order',
            'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']
