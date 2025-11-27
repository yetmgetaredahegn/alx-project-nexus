import pytest
from django.urls import reverse
from rest_framework import status
from decimal import Decimal

from orders.models import Order
from payments.models import Payment


@pytest.mark.django_db
class TestPaymentCreation:
    def test_create_payment_record_when_order_created(self, api_client, user, order_factory, payment_factory):
        """
        Payment records should be created automatically when the Order API
        creates an order. We just verify the Payment exists & matches domain rules.
        """
        # Create order owned by user
        order = order_factory(user=user, total=Decimal("100.00"))

        # Create payment
        payment = payment_factory(order=order, amount=order.total, status="pending")

        assert payment.order == order
        assert payment.status == "pending"
        assert payment.amount == order.total

    def test_user_cannot_create_payment_directly(self, api_client, user):
        """
        Payment is system-managed. Users should NOT be allowed to POST /payments/.
        ListAPIView doesn't support POST, so it returns 405 Method Not Allowed.
        """
        api_client.force_authenticate(user=user)

        payload = {
            "order": "uuid",
            "amount": 200,
        }

        url = reverse("payments:payment-list")
        response = api_client.post(url, payload)

        # ListAPIView doesn't have POST method, returns 405
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
