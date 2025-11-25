import pytest
import tempfile
from PIL import Image
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


def generate_image_file():
    file = tempfile.NamedTemporaryFile(suffix=".png")
    image = Image.new("RGB", (100, 100))
    image.save(file, "PNG")
    file.seek(0)
    return file


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser",
        password="password123",
        email="test@mail.com",
    )


@pytest.fixture
def admin(db):
    return User.objects.create_superuser(
        username="admin",
        password="admin123",
        email="admin@mail.com",
    )


@pytest.mark.django_db
class TestMyProfile:
    """Test cases for /api/accounts/profiles/me/ endpoint"""
    
    def test_get_my_profile(self, client, user):
        client.force_authenticate(user)
        url = reverse("profile-me")

        response = client.get(url)
        assert response.status_code == 200

    def test_patch_update_profile(self, client, user):
        client.force_authenticate(user)
        url = reverse("profile-me")

        img = generate_image_file()
        data = {
            "phone": "0911002200",
            "bio": "New bio",
            "avatar": img,
        }

        response = client.patch(url, data, format="multipart")
        assert response.status_code == 200
        assert response.data["bio"] == "New bio"

    def test_put_update_profile(self, client, user):
        client.force_authenticate(user)
        url = reverse("profile-me")

        data = {
            "phone": "0911002200",
            "bio": "Full update bio",
        }

        response = client.put(url, data, format="json")
        assert response.status_code == 200
        assert response.data["bio"] == "Full update bio"


@pytest.mark.django_db
class TestProfilePermissions:
    """Test cases for profile permissions and admin access"""
    
    def test_non_admin_cannot_list_profiles(self, client, user):
        client.force_authenticate(user)
        url = reverse("profile-list")

        response = client.get(url)
        assert response.status_code == 403

    def test_admin_can_list_profiles(self, client, admin):
        client.force_authenticate(admin)
        url = reverse("profile-list")

        response = client.get(url)
        assert response.status_code == 200

    def test_non_admin_cannot_delete_profiles(self, client, user):
        client.force_authenticate(user)
        url = reverse("profile-detail", args=[user.profile.id])

        response = client.delete(url)
        assert response.status_code == 403