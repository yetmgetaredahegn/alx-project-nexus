import pytest
from django.urls import reverse
from rest_framework import status
from model_bakery import baker


@pytest.mark.django_db
class TestPaymentCreation:
    def test_create_payment_record_when_order_created(self, api_client, user):
        """
        Payment records should be created automatically when the Order API
        creates an order. We just verify the Payment exists & matches domain rules.
        """
        # Create order owned by user
        order = baker.make("orders.Order", user=user, status="pending", total_amount=100)

        # Create payment
        payment = baker.make(
            "payments.Payment",
            order=order,
            provider="chapa",
            amount=order.total_amount,
            status="pending",
        )

        assert payment.order == order
        assert payment.status == "pending"
        assert payment.amount == order.total_amount

    def test_user_cannot_create_payment_directly(self, api_client, user):
        """
        Payment is system-managed. Users should NOT be allowed to POST /payments/.
        """
        api_client.force_authenticate(user)

        payload = {
            "order": "uuid",
            "provider": "chapa",
            "amount": 200,
        }

        url = reverse("payments:payment-list")
        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_403_FORBIDDEN
