import pytest
from django.urls import reverse

@pytest.mark.django_db
class TestOrderCreate:
    def test_requires_auth(self, api_client):
        url = reverse("orders:order-list")
        payload = {"shipping_address_id": "uuid", "payment_method": "chapa"}

        response = api_client.post(url, payload)
        assert response.status_code == 401

    def test_fails_if_cart_empty(self, authenticated_client):
        url = reverse("orders:order-list")

        payload = {
            "shipping_address_id": "11111111-1111-1111-1111-111111111111",
            "payment_method": "chapa",
        }

        response = authenticated_client.post(url, payload)
        assert response.status_code == 400
        assert "cart" in response.data["detail"].lower() or "empty" in response.data["detail"].lower()

    def test_creates_order_successfully(
        self, authenticated_client, cart_with_items, user, product_factory
    ):
        url = reverse("orders:order-list")

        payload = {
            "shipping_address_id": "11111111-1111-1111-1111-111111111111",
            "payment_method": "chapa",
        }

        response = authenticated_client.post(url, payload)

        assert response.status_code == 201
        assert response.data["status"] == "pending"
        assert "id" in response.data

    def test_clears_cart_after_order(
        self, authenticated_client, cart_with_items, cart_model
    ):
        url = reverse("orders:order-list")
        payload = {
            "shipping_address_id": "11111111-1111-1111-1111-111111111111",
            "payment_method": "chapa",
        }

        authenticated_client.post(url, payload)

        cart = cart_model.objects.get(user=cart_with_items.user)
        assert cart.items.count() == 0
