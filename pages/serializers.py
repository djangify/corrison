# pages/serializers.py
from rest_framework import serializers
from .models import Page, PageFeature, Testimonial, PageTestimonial
from core.utils import process_content_media_urls


class TestimonialSerializer(serializers.ModelSerializer):
    """Serializer for testimonial data"""

    class Meta:
        model = Testimonial
        fields = [
            "id",
            "name",
            "title",
            "company",
            "content",
            "image",
            "rating",
            "category",
            "is_featured",
            "order",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Process the content field for embedded media URLs
        if "content" in data and data["content"]:
            data["content"] = process_content_media_urls(data["content"])

        return data


class PageTestimonialSerializer(serializers.ModelSerializer):
    """Serializer for page-testimonial relationship with full testimonial data"""

    testimonial = TestimonialSerializer(read_only=True)

    class Meta:
        model = PageTestimonial
        fields = ["id", "testimonial", "order"]


class PageFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageFeature
        fields = ["id", "title", "content", "icon", "order"]

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Process the content field for embedded media URLs
        if "content" in data and data["content"]:
            data["content"] = process_content_media_urls(data["content"])

        return data


class PageSerializer(serializers.ModelSerializer):
    hero_image = serializers.ImageField(read_only=True)
    features = PageFeatureSerializer(many=True, read_only=True)
    testimonials = PageTestimonialSerializer(
        source="page_testimonials", many=True, read_only=True
    )

    # Computed fields for convenience
    hero_image_src = serializers.SerializerMethodField()
    is_landing_page = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = [
            # Basic fields
            "id",
            "slug",
            "title",
            "subtitle",
            "content",
            "meta_description",
            "is_published",
            "order",
            "created_at",
            "updated_at",
            # Page type
            "page_type",
            "is_landing_page",
            # Hero section - basic
            "hero_title",
            "hero_subtitle",
            "hero_content",
            "hero_image",
            "hero_image_src",
            "hero_image_url",
            "hero_right_content",
            # Hero section - CTAs
            "hero_button_text",
            "hero_button_url",
            "hero_button_2_text",
            "hero_button_2_url",
            # Landing page features
            "hero_video_url",
            "show_prelaunch_badge",
            "prelaunch_badge_text",
            "show_countdown",
            "countdown_target_date",
            "countdown_title",
            "show_social_proof",
            "social_proof_title",
            "show_scroll_indicator",
            # Content sections
            "middle_section_title",
            "middle_section_content",
            "end_section_title",
            "end_section_content",
            # Features
            "has_feature_section",
            "feature_section_title",
            "features",
            # Testimonials
            "testimonials",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_hero_image_src(self, obj):
        """Get the hero image source URL"""
        return obj.hero_image_src()

    def get_is_landing_page(self, obj):
        """Check if this is a landing page"""
        return obj.is_landing_page()

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Process content fields for embedded media URLs
        content_fields = [
            "content",
            "hero_content",
            "hero_right_content",
            "middle_section_content",
            "end_section_content",
        ]
        for field in content_fields:
            if field in data and data[field]:
                data[field] = process_content_media_urls(data[field])

        return data


class PageListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for page lists"""

    hero_image_src = serializers.SerializerMethodField()
    is_landing_page = serializers.SerializerMethodField()
    testimonial_count = serializers.SerializerMethodField()
    feature_count = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = [
            "id",
            "slug",
            "title",
            "subtitle",
            "page_type",
            "is_landing_page",
            "hero_title",
            "hero_image_src",
            "meta_description",
            "is_published",
            "order",
            "created_at",
            "updated_at",
            "testimonial_count",
            "feature_count",
        ]

    def get_hero_image_src(self, obj):
        """Get the hero image source URL"""
        return obj.hero_image_src()

    def get_is_landing_page(self, obj):
        """Check if this is a landing page"""
        return obj.is_landing_page()

    def get_testimonial_count(self, obj):
        """Get count of testimonials for this page"""
        return obj.page_testimonials.count()

    def get_feature_count(self, obj):
        """Get count of features for this page"""
        return obj.features.count()
