from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Profile  # Correct import - it's Profile, not UserProfile

User = get_user_model()


class Command(BaseCommand):
    help = "Fix user profiles"

    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, help="User email")
        parser.add_argument("--username", type=str, help="Username")

    def handle(self, *args, **options):
        email = options.get("email", "corrison@corrisonapi.com")
        username = options.get("username")

        try:
            # Find user by email or username
            if username:
                user = User.objects.get(username=username)
            else:
                user = User.objects.get(email=email)

            self.stdout.write(f"Found user: {user.username} ({user.email})")

            # Check user attributes
            self.stdout.write(f"  Is active: {user.is_active}")
            self.stdout.write(f"  Is staff: {user.is_staff}")
            self.stdout.write(f"  Is superuser: {user.is_superuser}")

            # Check if user has profile
            if hasattr(user, "profile"):
                profile = user.profile
                self.stdout.write("\nProfile exists:")
                self.stdout.write(f"  Email verified: {profile.email_verified}")
                self.stdout.write(f"  Phone: {profile.phone or 'Not set'}")
                self.stdout.write(f"  Birth date: {profile.birth_date or 'Not set'}")
                self.stdout.write(f"  Email marketing: {profile.email_marketing}")
                self.stdout.write(
                    f"  Receive order updates: {profile.receive_order_updates}"
                )
            else:
                # Create profile if missing
                self.stdout.write("\nNo profile found! Creating one...")
                profile = Profile.objects.create(
                    user=user,
                    email_verified=user.is_superuser,  # Auto-verify superusers
                )
                self.stdout.write(f"Created profile for {user.email}")
                self.stdout.write(f"  Email verified: {profile.email_verified}")

            # Verify user is active
            if not user.is_active:
                user.is_active = True
                user.save()
                self.stdout.write("\nActivated user")

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User not found: {email or username}"))
