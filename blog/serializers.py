from rest_framework import serializers
from .models import BlogPost

class BlogPostSerializer(serializers.ModelSerializer):
    featured_image = serializers.ImageField(read_only=True)
    attachment     = serializers.FileField(read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            'id',
            'title',
            'slug',
            'content',
            'created_at',
            'featured_image',
            'youtube_url',
            'attachment',
            'is_featured',
        ]
        read_only_fields = ['id', 'slug', 'created_at']
