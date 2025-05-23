# pages/serializers.py
from rest_framework import serializers
from .models import Page, PageFeature


class PageFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageFeature
        fields = ['id', 'title', 'content', 'icon', 'order']


class PageSerializer(serializers.ModelSerializer):
    hero_image = serializers.ImageField(read_only=True)
    features = PageFeatureSerializer(many=True, read_only=True)

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
            'created_at',
            'hero_title',
            'hero_subtitle',
            'hero_content',
            'hero_right_content',
            'hero_button_text',
            'hero_button_url',
            'middle_section_title',
            'middle_section_content',
            'end_section_title',
            'end_section_content',
            'has_feature_section',
            'feature_section_title',
            'features',
        ]
        read_only_fields = ['id', 'updated_at', 'created_at']
