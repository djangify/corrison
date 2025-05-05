# linkpage/serializers.py
from rest_framework import serializers
from .models import LinkHub, Link

class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = ['id', 'title', 'url', 'icon_url', 'order']

class LinkHubSerializer(serializers.ModelSerializer):
    links = LinkSerializer(many=True, read_only=True)

    class Meta:
        model  = LinkHub
        fields = ['id', 'slug', 'title', 'description', 'links']
        lookup_field = 'slug'
