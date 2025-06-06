from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import Profile, WishlistItem


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "Profile"
    readonly_fields = ("email_verification_token", "email_verification_sent_at")
    extra = 0  # Don't show extra empty forms
    max_num = 1  # Only allow one profile per user

    def get_queryset(self, request):
        """Ensure we get the existing profile if it exists"""
        qs = super().get_queryset(request)
        return qs

    def has_add_permission(self, request, obj=None):
        """Only allow adding profile if user doesn't have one"""
        if obj and hasattr(obj, "profile"):
            return False
        return super().has_add_permission(request, obj)


class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "email_verified_status",
        "date_joined",
    )

    def email_verified_status(self, obj):
        if hasattr(obj, "profile") and obj.profile.email_verified:
            return format_html('<span style="color: green;">✓ Verified</span>')
        return format_html('<span style="color: red;">✗ Not Verified</span>')

    email_verified_status.short_description = "Email Status"

    def save_model(self, request, obj, form, change):
        """Save the user first, then handle profile via signal"""
        super().save_model(request, obj, form, change)

        # Ensure profile exists (signal should handle this, but just in case)
        if not hasattr(obj, "profile"):
            Profile.objects.get_or_create(
                user=obj, defaults={"email_verified": obj.is_superuser}
            )


# Re-register UserAdmin with the updated class
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "phone",
        "email_verified",
        "email_marketing",
        "receive_order_updates",
    )
    list_filter = ("email_verified", "email_marketing", "receive_order_updates")
    search_fields = ("user__username", "user__email", "phone")
    raw_id_fields = ("user",)
    readonly_fields = ("email_verification_token", "email_verification_sent_at")

    fieldsets = (
        (None, {"fields": ("user", "phone", "birth_date")}),
        (
            "Email Verification",
            {
                "fields": (
                    "email_verified",
                    "email_verification_token",
                    "email_verification_sent_at",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Preferences", {"fields": ("email_marketing", "receive_order_updates")}),
    )


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__email", "user__username", "product__name")
    date_hierarchy = "created_at"
