# accounts/management/commands/send_verification_emails.py
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from accounts.utils import send_verification_email
from django.utils import timezone


class Command(BaseCommand):
    help = "Send verification emails to all unverified users"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without actually sending emails",
        )
        parser.add_argument(
            "--email",
            type=str,
            help="Send verification email to a specific user email address",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Send emails even to users who already have verification tokens",
        )

    def handle(self, *args, **options):
        self.stdout.write("Starting verification email process...")

        # Determine which users to target
        if options["email"]:
            # Target specific user
            try:
                user = User.objects.get(email=options["email"])
                users = [user]
                self.stdout.write("Targeting specific user: {}".format(user.email))
            except User.DoesNotExist:
                raise CommandError(
                    "User with email '{}' not found".format(options["email"])
                )
        else:
            # Target all unverified users
            users = User.objects.filter(profile__email_verified=False).select_related(
                "profile"
            )

            self.stdout.write("Found {} unverified users".format(users.count()))

        if not users:
            self.stdout.write(self.style.WARNING("No unverified users found."))
            return

        # Show users that will be processed
        self.stdout.write("\nUsers to process:")
        for user in users:
            verification_status = (
                "✓ Has token" if user.profile.email_verification_token else "✗ No token"
            )
            sent_date = (
                user.profile.email_verification_sent_at.strftime("%Y-%m-%d %H:%M")
                if user.profile.email_verification_sent_at
                else "Never"
            )

            self.stdout.write(
                "  • {} ({}) - {} - Last sent: {}".format(
                    user.email,
                    user.get_full_name() or "No name",
                    verification_status,
                    sent_date,
                )
            )

        if options["dry_run"]:
            self.stdout.write(
                self.style.WARNING("\n🔍 DRY RUN - No emails will be sent")
            )
            return

        # Confirm before proceeding (unless targeting specific user)
        if not options["email"]:
            confirm = input(
                "Send verification emails to {} users? (y/N): ".format(len(users))
            )
            if confirm.lower() != "y":
                self.stdout.write("Operation cancelled.")
                return

        # Process users
        success_count = 0
        error_count = 0
        skipped_count = 0

        self.stdout.write(f"\n📧 Sending verification emails...")

        for user in users:
            try:
                profile = user.profile

                # Skip if user already has a recent token (unless --force is used)
                if (
                    profile.email_verification_token
                    and profile.email_verification_sent_at
                    and not options["force"]
                ):
                    # Check if token was sent in last 24 hours
                    time_diff = timezone.now() - profile.email_verification_sent_at
                    if time_diff.total_seconds() < 86400:  # 24 hours
                        self.stdout.write(
                            "  ⏭️  Skipping {} - verification email sent recently".format(
                                user.email
                            )
                        )
                        skipped_count += 1
                        continue

                # Generate new verification token
                token = profile.generate_verification_token()

                # Send verification email
                email_sent = send_verification_email(user, token)

                if email_sent:
                    self.stdout.write("  ✅ Sent to {}".format(user.email))
                    success_count += 1
                else:
                    self.stdout.write("  ❌ Failed to send to {}".format(user.email))
                    error_count += 1

            except Exception as e:
                self.stdout.write(
                    "  ❌ Error processing {}: {}".format(user.email, str(e))
                )
                error_count += 1

        # Summary
        self.stdout.write("\n Summary:")
        self.stdout.write("   Successfully sent: {}".format(success_count))
        if skipped_count > 0:
            self.stdout.write("  ⏭  Skipped: {}".format(skipped_count))
        if error_count > 0:
            self.stdout.write("   Errors: {}".format(error_count))

        if success_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "\n🎉 Successfully sent {} verification emails!".format(
                        success_count
                    )
                )
            )
        elif error_count > 0:
            self.stdout.write(
                self.style.ERROR("\n  Completed with {} errors".format(error_count))
            )
        else:
            self.stdout.write(self.style.WARNING("\n  No emails were sent"))
