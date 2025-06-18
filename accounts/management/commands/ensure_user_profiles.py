# Create a management command: management/commands/ensure_user_profiles.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Profile


class Command(BaseCommand):
    help = "Ensures all users have profiles"

    def handle(self, *args, **options):
        users_without_profiles = User.objects.filter(profile__isnull=True)
        created_count = 0

        for user in users_without_profiles:
            Profile.objects.create(
                user=user,
                email_verified=user.is_superuser,  # Auto-verify superusers
            )
            created_count += 1
            self.stdout.write(f"Created profile for user: {user.username}")

        self.stdout.write(
            self.style.SUCCESS(f"Successfully created {created_count} profiles")
        )
