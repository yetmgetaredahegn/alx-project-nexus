import pytest
from django.urls import reverse
from rest_framework import status

from payments.models import Payment


@pytest.mark.django_db
class TestPaymentPermissions:
    def test_user_can_view_only_his_payments(self, api_client, user, payment_factory, order_factory):
        # Create payment for the user
        my_order = order_factory(user=user)
        my_payment = payment_factory(order=my_order)
        
        # Create payment for another user
        from django.contrib.auth import get_user_model
        User = get_user_model()
        other_user = User.objects.create_user(
            username="otheruser",
            email="other@test.com",
            password="pass12345"
        )
        other_order = order_factory(user=other_user)
        other_payment = payment_factory(order=other_order)

        api_client.force_authenticate(user=user)

        url = reverse("payments:payment-list")
        res = api_client.get(url)

        ids = [str(p["id"]) for p in res.data["results"]]

        assert str(my_payment.id) in ids
        assert str(other_payment.id) not in ids

    def test_admin_can_view_their_payments(self, api_client, admin_user, payment_factory, order_factory):
        # Create payments for admin user's orders
        admin_order1 = order_factory(user=admin_user)
        admin_order2 = order_factory(user=admin_user)
        p1 = payment_factory(order=admin_order1)
        p2 = payment_factory(order=admin_order2)

        api_client.force_authenticate(user=admin_user)

        url = reverse("payments:payment-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        ids = [str(p["id"]) for p in response.data["results"]]
        assert str(p1.id) in ids
        assert str(p2.id) in ids
