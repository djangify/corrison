# accounts/management/commands/fix_superuser_verification.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Profile


class Command(BaseCommand):
    help = "Fix email verification status for superusers"

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            help="Specific username to fix (optional, fixes all superusers if not provided)",
        )
        parser.add_argument(
            "--verify-all-staff",
            action="store_true",
            help="Also verify email for all staff users",
        )

    def handle(self, *args, **options):
        username = options.get("username")
        verify_staff = options.get("verify_all_staff", False)

        if username:
            # Fix specific user
            try:
                user = User.objects.get(username=username)
                self.fix_user_verification(user)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User "{username}" not found'))
        else:
            # Fix all superusers
            superusers = User.objects.filter(is_superuser=True)
            self.stdout.write(f"Found {superusers.count()} superuser(s)")

            for user in superusers:
                self.fix_user_verification(user)

            # Optionally fix staff users
            if verify_staff:
                staff_users = User.objects.filter(is_staff=True, is_superuser=False)
                self.stdout.write(f"Found {staff_users.count()} staff user(s)")

                for user in staff_users:
                    self.fix_user_verification(user)

    def fix_user_verification(self, user):
        """Fix email verification for a specific user"""
        try:
            profile = user.profile
            if not profile.email_verified:
                profile.email_verified = True
                profile.email_verification_token = ""
                profile.email_verification_sent_at = None
                profile.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Fixed email verification for user "{user.username}" ({user.email})'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'- User "{user.username}" already verified')
                )
        except Profile.DoesNotExist:
            # Create profile if it doesn't exist
            Profile.objects.create(user=user, email_verified=True)
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Created profile and verified email for user "{user.username}"'
                )
            )
