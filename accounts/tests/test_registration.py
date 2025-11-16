import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_register_creates_profile(client):
    url = "/api/auth/users/"
    payload = {
        "email": "testuser@example.com",
        "username": "testuser",
        "password": "Testpass123!",
        "re_password": "Testpass123!"
    }

    response = client.post(url, payload, format="json")
    assert response.status_code == 201

    user = User.objects.get(email="testuser@example.com")
    assert hasattr(user, "profile")
