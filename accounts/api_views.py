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

from .models import Profile
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
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
    """Login user and return JWT tokens"""
    serializer = UserLoginSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.validated_data["user"]

        # Check if email is verified (optional - you can remove this check)
        if not user.profile.email_verified:
            return Response(
                {"error": "Please verify your email address before logging in."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            }
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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


@api_view(["GET"])
@permission_classes([AllowAny])
def verify_email(request, token):
    """Verify user email with token"""
    serializer = EmailVerificationSerializer(data={"token": token})

    if serializer.is_valid():
        try:
            profile = Profile.objects.get(email_verification_token=token)

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
                send_welcome_email(profile.user)
            except Exception as e:
                print(f"Failed to send welcome email: {e}")

            return Response(
                {"message": "Email verified successfully! Welcome to Corrison."}
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
    """Resend verification email"""
    serializer = ResendVerificationSerializer(data=request.data)

    if serializer.is_valid():
        email = serializer.validated_data["email"]
        user = User.objects.get(email=email)

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

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Get or update user profile"""
    if request.method == "GET":
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    elif request.method == "PUT":
        serializer = ProfileUpdateSerializer(
            request.user.profile, data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Profile updated successfully.",
                    "user": UserSerializer(request.user).data,
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
