# pages/serializers.py
from rest_framework import serializers
from .models import Page, PageFeature, Testimonial, PageTestimonial


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
