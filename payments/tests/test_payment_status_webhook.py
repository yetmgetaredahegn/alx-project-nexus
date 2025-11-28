import pytest
import json
import hmac
import hashlib
from django.urls import reverse
from django.conf import settings
from rest_framework import status

from orders.models import Order


@pytest.mark.django_db
class TestPaymentWebhook:
    def test_webhook_confirms_payment(self, api_client, payment_factory):
        """
        Chapa webhook marks payment = 'completed' and order.payment_status = 'paid'
        """
        payment = payment_factory(status="pending")
        order = payment.order

        url = reverse("payments:payment-webhook")
        payload = {
            "tx_ref": payment.tx_ref,
            "status": "success",
            "email": order.user.email,
            "amount": str(payment.amount),
        }

        # Create HMAC signature
        body = json.dumps(payload).encode()
        secret_key = settings.CHAPA_SECRET_KEY or "test_secret_key_for_webhook"
        signature = hmac.new(
            secret_key.encode(),
            msg=body,
            digestmod=hashlib.sha256
        ).hexdigest()

        response = api_client.post(
            url,
            data=body,
            content_type="application/json",
            HTTP_CHAPA_SIGNATURE=signature
        )

        payment.refresh_from_db()
        order.refresh_from_db()

        assert response.status_code == status.HTTP_200_OK
        assert payment.status == "completed"
        assert order.payment_status == Order.PAYMENT_PAID

    def test_webhook_handles_failed_payment(self, api_client, payment_factory):
        payment = payment_factory(status="pending")
        order = payment.order

        url = reverse("payments:payment-webhook")
        payload = {
            "tx_ref": payment.tx_ref,
            "status": "failed",
            "email": order.user.email,
            "amount": str(payment.amount),
        }

        # Create HMAC signature
        body = json.dumps(payload).encode()
        secret_key = settings.CHAPA_SECRET_KEY or "test_secret_key_for_webhook"
        signature = hmac.new(
            secret_key.encode(),
            msg=body,
            digestmod=hashlib.sha256
        ).hexdigest()

        response = api_client.post(
            url,
            data=body,
            content_type="application/json",
            HTTP_CHAPA_SIGNATURE=signature
        )

        payment.refresh_from_db()
        order.refresh_from_db()

        assert response.status_code == status.HTTP_200_OK
        assert payment.status == "failed"
        assert order.payment_status == Order.PAYMENT_FAILED
