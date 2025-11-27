import pytest
from django.urls import reverse
from rest_framework import status
from model_bakery import baker


@pytest.mark.django_db
class TestPaymentPermissions:
    def test_user_can_view_only_his_payments(self, api_client, user):
        my_payment = baker.make("payments.Payment", order__user=user)
        other_payment = baker.make("payments.Payment")

        api_client.force_authenticate(user)

        url = reverse("payments:payment-list")
        res = api_client.get(url)

        ids = [p["id"] for p in res.data["results"]]

        assert my_payment.id in ids
        assert other_payment.id not in ids

    def test_admin_can_view_all_payments(self, api_client, admin_user):
        p1 = baker.make("payments.Payment")
        p2 = baker.make("payments.Payment")

        api_client.force_authenticate(admin_user)

        url = reverse("payments:payment-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 2
