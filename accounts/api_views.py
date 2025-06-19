# accounts/api_views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import authenticate, login as django_login
from .models import Profile
from .serializers import (
    UserRegistrationSerializer,
    EmailVerificationSerializer,
    ResendVerificationSerializer,
    ChangePasswordSerializer,
    ProfileUpdateSerializer,
    UserSerializer,
)
from .utils import send_verification_email, send_welcome_email


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """Register a new user and send verification email"""
    serializer = UserRegistrationSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()

        # Generate verification token
        profile = user.profile
        token = profile.generate_verification_token()

        # Send verification email
        try:
            send_verification_email(user, token)
        except Exception as e:
            # Log error but don't fail registration
            print(f"Failed to send verification email: {e}")

        return Response(
            {
                "message": "Registration successful. Please check your email to verify your account.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """
    Login endpoint that accepts either username or email.
    Returns JWT tokens for authentication.
    """
    # Get the username/email and password from request
    username_or_email = request.data.get("username", "").strip()
    password = request.data.get("password", "")

    # Check if username field might actually be an email
    if not username_or_email:
        # Try getting from 'email' field as well
        username_or_email = request.data.get("email", "").strip()

    if not username_or_email or not password:
        return Response(
            {"non_field_errors": ["Username/email and password are required."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Try to get the user by username or email
    user = None

    # Check if it looks like an email
    if "@" in username_or_email:
        # Try to find user by email
        try:
            user_obj = User.objects.get(email__iexact=username_or_email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            pass
    else:
        # Try standard username authentication
        user = authenticate(request, username=username_or_email, password=password)

    if user is not None:
        django_login(request, user)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        # Get user profile data
        profile = hasattr(user, "profile") and user.profile

        # Return user data with JWT tokens
        return Response(
            {
                "success": True,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email_verified": profile.email_verified if profile else False,
                    "is_staff": user.is_staff,
                    "is_superuser": user.is_superuser,
                },
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        )
    else:
        return Response(
            {"non_field_errors": ["Unable to log in with provided credentials."]},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    """Logout user by blacklisting refresh token"""
    try:
        refresh_token = request.data.get("refresh")
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()

        return Response({"message": "Successfully logged out."})
    except Exception as e:
        return Response({"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_email(request):
    """Verify user's email with token"""
    serializer = EmailVerificationSerializer(data=request.data)

    if serializer.is_valid():
        token = serializer.validated_data["token"]

        try:
            # Find profile with this token
            profile = Profile.objects.get(email_verification_token=token)

            # Get the user from the profile
            user = profile.user

            # Check token expiry
            if profile.email_verification_sent_at:
                expiry_time = profile.email_verification_sent_at + timedelta(
                    hours=getattr(settings, "EMAIL_VERIFICATION_TOKEN_EXPIRY", 24)
                )
                if timezone.now() > expiry_time:
                    return Response(
                        {
                            "error": "Verification token has expired. Please request a new one."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Verify email
            profile.email_verified = True
            profile.email_verification_token = ""
            profile.email_verification_sent_at = None
            profile.save()

            # Send welcome email
            try:
                send_welcome_email(user)
            except Exception as e:
                # Log error but continue
                print(f"Failed to send welcome email: {e}")

            # Send download ready emails for any pending digital orders
            from checkout.models import OrderItem
            from accounts.utils import send_download_ready_email

            try:
                # Find all digital items for this user
                digital_items = OrderItem.objects.filter(
                    order__user=user, is_digital=True, download_token__isnull=False
                ).select_related("order")

                for item in digital_items:
                    send_download_ready_email(item, user)
            except Exception as e:
                # Log error but continue
                print(f"Failed to send download ready emails: {e}")

            # Generate JWT tokens for auto-login after verification
            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "message": "Email verified successfully. You can now access all features.",
                    "tokens": {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    },
                    "user": UserSerializer(user).data,
                }
            )

        except Profile.DoesNotExist:
            return Response(
                {"error": "Invalid verification token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def resend_verification(request):
    """Resend verification email - works for both authenticated and unauthenticated users"""

    # If user is authenticated, use their email
    if request.user.is_authenticated:
        user = request.user

        # Check if already verified
        if hasattr(user, "profile") and user.profile.email_verified:
            return Response(
                {"error": "Email is already verified."},
                status=status.HTTP_400_BAD_REQUEST,
            )
    else:
        # For unauthenticated users, require email in request
        serializer = ResendVerificationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "No user found with this email address."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # Generate new verification token
    token = user.profile.generate_verification_token()

    # Send verification email
    try:
        send_verification_email(user, token)
        return Response({"message": "Verification email sent successfully."})
    except Exception as e:
        return Response(
            {"error": "Failed to send verification email. Please try again later."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Get or update user profile"""
    if request.method == "GET":
        # Get user profile data
        user = request.user
        profile = hasattr(user, "profile") and user.profile

        # Build response data manually to ensure email_verified is included
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email_verified": profile.email_verified if profile else False,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
        }

        # Add profile data if it exists
        if profile:
            user_data["profile"] = {
                "phone": profile.phone,
                "birth_date": profile.birth_date,
                "email_marketing": profile.email_marketing,
                "receive_order_updates": profile.receive_order_updates,
                "email_verified": profile.email_verified,
            }

        return Response(user_data)

    elif request.method == "PUT":
        serializer = ProfileUpdateSerializer(
            request.user.profile, data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()

            # Return updated user data with email_verified
            user = request.user
            profile = user.profile

            user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email_verified": profile.email_verified,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
            }

            return Response(
                {
                    "message": "Profile updated successfully.",
                    "user": user_data,
                }
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change user password"""
    serializer = ChangePasswordSerializer(
        data=request.data, context={"request": request}
    )

    if serializer.is_valid():
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response({"message": "Password changed successfully."})

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
