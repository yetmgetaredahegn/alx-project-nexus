import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from cart.models import Cart, CartItem

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="pass1234",
    )


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def cart(user):
    return Cart.objects.create(user=user)


@pytest.fixture
def category(db):
    from catalog.models import Category
    return Category.objects.create(name="Clothes")


@pytest.fixture
def product(category):
    from catalog.models import Product
    return Product.objects.create(
        category=category,
        title="T-Shirt",
        price=50,
        stock_quantity=10
    )


@pytest.fixture
def cart_item(cart, product):
    return CartItem.objects.create(
        cart=cart,
        product=product,
        quantity=1,
        unit_price=product.price
    )


# -------------------------
#   CART VIEWSET TESTS
# -------------------------
class TestCartView:
    def test_get_cart(self, auth_client, cart, cart_item):
        url = reverse("cart-detail")

        response = auth_client.get(url)

        assert response.status_code == 200
        assert response.data["id"] == cart.id
        assert len(response.data["items"]) == 1
        assert response.data["items"][0]["quantity"] == 1
        assert response.data["total"] == "50.00"

    def test_clear_cart(self, auth_client, cart, cart_item):
        url = reverse("cart-clear")

        response = auth_client.delete(url)

        assert response.status_code == 204
        assert CartItem.objects.count() == 0
