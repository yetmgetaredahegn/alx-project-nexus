import pytest
from django.urls import reverse

@pytest.mark.django_db
class TestOrderDetail:
    def test_only_owner_or_admin_can_view(
        self, authenticated_client, user, other_user, order_factory
    ):
        order = order_factory(user=other_user)
        url = reverse("orders:order-detail", args=[order.id])

        response = authenticated_client.get(url)
        assert response.status_code == 403

    def test_owner_can_view(self, authenticated_client, user, order_factory):
        order = order_factory(user=user)
        url = reverse("orders:order-detail", args=[order.id])

        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert response.data["id"] == order.id

    def test_admin_can_update_status(self, admin_client, order_factory):
        order = order_factory()
        url = reverse("orders:order-detail", args=[order.id])

        response = admin_client.patch(url, {"status": "shipped"})
        assert response.status_code == 200
        assert response.data["status"] == "shipped"

    def test_normal_user_cannot_update_status(self, authenticated_client, order_factory):
        order = order_factory()
        url = reverse("orders:order-detail", args=[order.id])

        response = authenticated_client.patch(url, {"status": "shipped"})
        assert response.status_code == 403

    def test_cancel_order_user(self, authenticated_client, user, order_factory):
        order = order_factory(user=user)
        url = reverse("orders:order-cancel", args=[order.id])

        response = authenticated_client.post(url, {"reason": "wrong item"})
        assert response.status_code == 200
        assert "id" in response.data
        assert response.data["order"] == order.id
