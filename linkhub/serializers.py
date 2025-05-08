from rest_framework import serializers
from .models import LinkHub, Link

class LinkSerializer(serializers.ModelSerializer):
    media_type_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Link
        fields = [
            'id', 
            'title', 
            'url', 
            'icon_url', 
            'media_type',
            'media_type_display',
            'description',
            'author',
            'order'
        ]
    
    def get_media_type_display(self, obj):
        return dict(Link.MEDIA_TYPES).get(obj.media_type, 'Link')

class LinkHubSerializer(serializers.ModelSerializer):
    links = LinkSerializer(many=True, read_only=True)

    class Meta:
        model = LinkHub
        fields = [
            'id', 
            'slug', 
            'title', 
            'description',
            'order', 
            'links'
        ]
        lookup_field = 'slug'