import uuid
import hmac
import json
import hashlib
import requests

from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiTypes,
)

from orders.models import Order
from .models import Payment
from .serializers import PaymentSerializer
from .tasks import send_payment_confirmation_email

@extend_schema(
    summary="Initiate a payment for an order",
    description=(
        "Initializes a Chapa payment for the user's order. "
        "Creates a Payment record and returns a redirect URL."
    ),
    tags=["Payments"],
    request=OpenApiTypes.OBJECT,
    examples=[
        OpenApiExample(
            name="Payment initiation",
            value={
                "order_id": "uuid-of-order",
                "return_url": "https://example.com/thank-you"
            }
        )
    ],
    responses={
        200: OpenApiTypes.OBJECT,
        400: OpenApiTypes.OBJECT,
        404: OpenApiTypes.OBJECT,
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def initiate_payment(request):
    order_id = request.data.get("order_id")
    return_url = request.data.get("return_url") or settings.PAYMENT_RETURN_URL

    if not order_id:
        return Response({"detail": "order_id is required"}, status=400)

    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({"detail": "Order not found"}, status=404)

    # Check if payment already exists
    if hasattr(order, "payment"):
        if order.payment.status == "completed":
            return Response({"detail": "Order already paid"}, status=400)
        # If payment exists but is pending or failed, we can reuse it or create new one
        # For simplicity, we'll return the existing payment URL if pending
        if order.payment.status == "pending":
            return Response({
                "detail": "Payment already initiated",
                "payment_id": str(order.payment.id),
                "tx_ref": order.payment.tx_ref,
            }, status=400)

    tx_ref = str(uuid.uuid4())

    payment = Payment.objects.create(
        order=order,
        tx_ref=tx_ref,
        amount=order.total,
        currency="ETB"
    )

    chapa_payload = {
        "amount": str(order.total),
        "currency": "ETB",
        "email": request.user.email,
        "first_name": request.user.first_name or "",
        "last_name": request.user.last_name or "",
        "tx_ref": tx_ref,
        "callback_url": settings.PAYMENT_CALLBACK_URL,
        "return_url": return_url,
    }

    headers = {
        "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
    }

    response = requests.post(
        f"{settings.CHAPA_BASE_URL}/transaction/initialize",
        headers=headers,
        data=chapa_payload
    )

    if response.status_code != 200:
        payment.mark_failed()
        return Response({"detail": "Failed to initialize payment"}, status=400)

    checkout_url = response.json()["data"]["checkout_url"]

    return Response({
        "payment_url": checkout_url,
        "payment_id": str(payment.id),
        "tx_ref": tx_ref,
    })

@extend_schema(
    summary="Chapa webhook callback",
    description="Handles Chapa payment status updates using HMAC signature verification.",
    tags=["Payments"],
    request=OpenApiTypes.OBJECT,
    responses={200: OpenApiTypes.OBJECT},
)
@csrf_exempt
@api_view(["POST"])
def chapa_webhook(request):
    signature = request.headers.get("chapa-signature")
    if not signature:
        return Response({"detail": "Missing signature"}, status=400)

    computed = hmac.new(
        settings.CHAPA_SECRET_KEY.encode(),
        msg=request.body,
        digestmod=hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, computed):
        return Response({"detail": "Invalid signature"}, status=403)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return Response({"detail": "Invalid JSON"}, status=400)

    tx_ref = payload.get("tx_ref")
    chapa_status = payload.get("status")
    email = payload.get("email")
    amount = payload.get("amount")

    if not tx_ref:
        return Response({"detail": "tx_ref missing"}, status=400)

    try:
        payment = Payment.objects.get(tx_ref=tx_ref)
    except Payment.DoesNotExist:
        return Response({"detail": "Payment not found"}, status=404)

    if chapa_status == "success":
        changed = payment.mark_completed()
        if changed:
            payment.order.payment_status = Order.PAYMENT_PAID
            payment.order.save(update_fields=["payment_status"])

            send_payment_confirmation_email.delay(
                email,
                amount,
                tx_ref
            )

    elif chapa_status == "failed":
        changed = payment.mark_failed()
        if changed:
            payment.order.payment_status = Order.PAYMENT_FAILED
            payment.order.save(update_fields=["payment_status"])

    return Response({"detail": "Webhook processed"}, status=200)


@extend_schema(
    summary="List payments for the authenticated user",
    tags=["Payments"],
    responses=PaymentSerializer(many=True),
)
class PaymentListView(ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(order__user=self.request.user)


@extend_schema(
    summary="Retrieve a single payment",
    tags=["Payments"],
    responses=PaymentSerializer,
)
class PaymentDetailView(RetrieveAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(order__user=self.request.user)
