import pytest
from django.urls import reverse

@pytest.mark.django_db
class TestOrderList:
    def test_requires_authentication(self, api_client):
        url = reverse("orders:order-list")
        response = api_client.get(url)
        assert response.status_code == 401

    def test_returns_only_user_orders(self, authenticated_client, order_factory, user, other_user):
        # Orders for the user
        order_factory(user=user)
        order_factory(user=user)

        # Order for another user
        order_factory(user=other_user)

        url = reverse("orders:order-list")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert len(response.data["results"]) == 2  # paginated
        assert all(item["user"] == user.id for item in response.data["results"])
