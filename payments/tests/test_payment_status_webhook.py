import pytest
from django.urls import reverse
from rest_framework import status
from model_bakery import baker


@pytest.mark.django_db
class TestPaymentWebhook:
    def test_webhook_confirms_payment(self, api_client):
        """
        Chapa webhook marks payment = 'paid' and order = 'paid'
        """
        payment = baker.make("payments.Payment", status="pending", provider="chapa")
        order = payment.order

        url = reverse("payments:webhook")
        payload = {
            "payment_id": str(payment.id),
            "status": "success",
            "amount": payment.amount,
        }

        response = api_client.post(url, payload, format="json")

        payment.refresh_from_db()
        order.refresh_from_db()

        assert response.status_code == status.HTTP_200_OK
        assert payment.status == "paid"
        assert order.status == "paid"

    def test_webhook_handles_failed_payment(self, api_client):
        payment = baker.make("payments.Payment", status="pending", provider="chapa")
        order = payment.order

        url = reverse("payments:webhook")
        payload = {
            "payment_id": str(payment.id),
            "status": "failed",
        }

        response = api_client.post(url, payload)

        payment.refresh_from_db()
        order.refresh_from_db()

        assert response.status_code == status.HTTP_200_OK
        assert payment.status == "failed"
        assert order.status == "payment_failed"
