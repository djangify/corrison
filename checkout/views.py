# checkout/views.py
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
from django.utils import timezone
from django.db import transaction
import mimetypes
import os
from .models import Order, OrderItem, Payment, OrderSettings
from api.serializers import OrderSerializer, PaymentSerializer
from .serializers import OrderSettingsSerializer
import stripe
import logging

logger = logging.getLogger(__name__)

# Set Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY


class OrderViewSet(viewsets.ModelViewSet):
    """
    Orders: authenticated users only - digital-only focus.
    """

    queryset = Order.objects.prefetch_related("items").all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class PaymentViewSet(viewsets.ModelViewSet):
    """
    Payments: authenticated users only.
    """

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(order__user=self.request.user)


@api_view(["GET"])
@permission_classes([AllowAny])
def check_payment_status(request):
    """
    Check payment status by payment intent ID.
    Used for order confirmation page.
    """
    payment_intent_id = request.GET.get("payment_intent")

    if not payment_intent_id:
        return Response(
            {"error": "Payment intent ID required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Retrieve payment intent from Stripe
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        # Check if order exists
        order = None
        try:
            order = Order.objects.get(stripe_payment_intent_id=payment_intent_id)
            order_data = OrderSerializer(order, context={"request": request}).data
        except Order.DoesNotExist:
            order_data = None

        return Response(
            {
                "payment_status": intent.status,
                "payment_amount": intent.amount / 100,  # Convert from cents
                "order": order_data,
                "success": intent.status == "succeeded",
            }
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error checking payment status: {str(e)}")
        return Response(
            {"error": "Unable to check payment status"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def download_product(request, token):
    """
    Download digital product file using download token.
    """
    # Get order item by download token
    order_item = get_object_or_404(OrderItem, download_token=token)

    # Check if download is allowed
    if not order_item.can_download:
        # Determine specific reason for denial
        if order_item.order.payment_status != "paid":
            return Response(
                {"error": "Order has not been paid"},
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

        if (
            order_item.download_expires_at
            and timezone.now() > order_item.download_expires_at
        ):
            return Response(
                {"error": "Download link has expired"}, status=status.HTTP_410_GONE
            )

        if (
            order_item.max_downloads
            and order_item.download_count >= order_item.max_downloads
        ):
            return Response(
                {"error": "Download limit exceeded"},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        if order_item.order.user and hasattr(order_item.order.user, "profile"):
            if not order_item.order.user.profile.email_verified:
                return Response(
                    {"error": "Email verification required"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        return Response(
            {"error": "Download not allowed"}, status=status.HTTP_403_FORBIDDEN
        )

    # Get the file to download
    digital_file = order_item.get_download_file()

    if not digital_file:
        return Response(
            {"error": "No file available for download"},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Get file path
    file_path = digital_file.path

    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)

    # Increment download count
    order_item.increment_download_count()

    # Log download
    logger.info(
        f"Download initiated for OrderItem {order_item.id} "
        f"(Order: {order_item.order.order_number}, "
        f"Product: {order_item.product_name}, "
        f"Count: {order_item.download_count}/{order_item.max_downloads or 'unlimited'})"
    )

    # Prepare file response
    try:
        # Open file
        file_handle = open(file_path, "rb")

        # Get file mimetype
        mimetype, _ = mimetypes.guess_type(file_path)
        if not mimetype:
            mimetype = "application/octet-stream"

        # Create response
        response = FileResponse(
            file_handle,
            content_type=mimetype,
            as_attachment=True,
            filename=os.path.basename(file_path),
        )

        # Add download headers
        response["Content-Disposition"] = (
            f'attachment; filename="{os.path.basename(file_path)}"'
        )
        response["X-Download-Count"] = str(order_item.download_count)

        if order_item.max_downloads:
            response["X-Downloads-Remaining"] = str(
                max(0, order_item.max_downloads - order_item.download_count)
            )

        return response

    except Exception as e:
        logger.error(f"Error serving file: {str(e)}")
        return Response(
            {"error": "Error serving file"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_downloads(request):
    """
    Get all digital downloads for authenticated user.
    """
    # Get all order items for digital products
    order_items = (
        OrderItem.objects.filter(
            order__user=request.user, is_digital=True, order__payment_status="paid"
        )
        .select_related("order", "product", "variant")
        .order_by("-created_at")
    )

    downloads = []
    for item in order_items:
        download_info = {
            "id": item.id,
            "order_number": item.order.order_number,
            "product_name": item.product_name,
            "variant_name": item.variant_name,
            "purchased_at": item.created_at,
            "download_count": item.download_count,
            "max_downloads": item.max_downloads,
            "download_expires_at": item.download_expires_at,
            "can_download": item.can_download,
            "download_url": None,
        }

        if item.can_download and item.download_token:
            download_info["download_url"] = request.build_absolute_uri(
                f"/api/v1/downloads/{item.download_token}/"
            )

        downloads.append(download_info)

    return Response({"downloads": downloads, "count": len(downloads)})


class OrderSettingsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for order settings - read-only access for all users
    """

    queryset = OrderSettings.objects.all()
    serializer_class = OrderSettingsSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        """Always return the first (and only) OrderSettings instance"""
        obj, created = OrderSettings.objects.get_or_create(pk=1)
        return obj
