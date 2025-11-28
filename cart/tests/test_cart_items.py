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
        username="carttester",
        email="user@example.com",
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
        stock_quantity=10,
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
#   CART ITEM TESTS
# -------------------------
class TestCartItemCreate:
    def test_add_item_to_cart(self, auth_client, product):
        url = reverse("cartitem-list")

        payload = {"product_id": product.id, "quantity": 2}

        response = auth_client.post(url, payload, format="json")

        assert response.status_code == 201
        assert response.data["product"]["id"] == product.id
        assert response.data["quantity"] == 2
        assert CartItem.objects.count() == 1

    def test_add_item_increments_existing(self, auth_client, cart, product):
        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=1,
            unit_price=product.price
        )

        url = reverse("cartitem-list")

        payload = {"product_id": product.id, "quantity": 3}

        auth_client.force_authenticate(user=cart.user)

        response = auth_client.post(url, payload, format="json")

        assert response.status_code == 201

        updated_item = CartItem.objects.get()
        assert updated_item.quantity == 4  # 1 + 3


class TestCartItemUpdate:
    def test_update_quantity(self, auth_client, cart_item):
        url = reverse("cartitem-detail", args=[cart_item.id])

        payload = {"quantity": 3}

        response = auth_client.patch(url, payload, format="json")

        assert response.status_code == 200
        cart_item.refresh_from_db()
        assert cart_item.quantity == 3


class TestCartItemDelete:
    def test_delete_cart_item(self, auth_client, cart_item):
        url = reverse("cartitem-detail", args=[cart_item.id])

        response = auth_client.delete(url)

        assert response.status_code == 204
        assert CartItem.objects.count() == 0
