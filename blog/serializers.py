# blog/serializers.py
from rest_framework import serializers
from .models import BlogCategory, BlogPost
from core.utils import process_content_media_urls


class BlogCategorySerializer(serializers.ModelSerializer):
    post_count = serializers.SerializerMethodField()

    class Meta:
        model = BlogCategory
        fields = ["id", "name", "slug", "description", "post_count"]

    def get_post_count(self, obj):
        return obj.posts.filter(status="published").count()


class BlogPostSerializer(serializers.ModelSerializer):
    category = BlogCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=BlogCategory.objects.all(),
        source="category",
        write_only=True,
        required=False,
        allow_null=True,
    )
    main_image_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    youtube_embed_url = serializers.SerializerMethodField()
    attachment_url = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "category",
            "category_id",
            "status",
            "is_featured",
            "published_at",
            "content",
            "featured_image",
            "external_image_url",
            "main_image_url",
            "thumbnail",
            "thumbnail_url",
            "youtube_url",
            "youtube_embed_url",
            "attachment",
            "attachment_url",
            "meta_title",
            "meta_description",
            "meta_keywords",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def get_main_image_url(self, obj):
        return obj.get_main_image_url()

    def get_thumbnail_url(self, obj):
        return obj.get_thumbnail_url()

    def get_youtube_embed_url(self, obj):
        return obj.get_youtube_embed_url()

    def get_attachment_url(self, obj):
        if obj.attachment:
            return obj.attachment.url
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Process the content field for embedded media URLs
        if "content" in data and data["content"]:
            data["content"] = process_content_media_urls(data["content"])

        return data
