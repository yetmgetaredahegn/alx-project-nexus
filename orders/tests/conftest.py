import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from cart.models import Cart
from orders.models import Order
from catalog.models import Product

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser",
        email="user@test.com",
        password="pass12345"
    )

@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        username="otheruser",
        email="other@test.com",
        password="pass12345"
    )

@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin",
        email="admin@test.com",
        password="pass12345"
    )

@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client

@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client

@pytest.fixture
def product_factory():
    def create(**kwargs):
        from catalog.models import Category
        # Create a default category if not provided
        if "category" not in kwargs:
            category, _ = Category.objects.get_or_create(name="Test Category", defaults={"is_active": True})
            kwargs["category"] = category
        default = {
            "title": "Test Product",
            "price": 100,
            "stock_quantity": 10,
        }
        default.update(kwargs)
        return Product.objects.create(**default)
    return create

@pytest.fixture
def cart_model():
    return Cart

@pytest.fixture
def cart_with_items(user, product_factory, cart_model):
    cart = cart_model.objects.create(user=user)
    product = product_factory()

    cart.items.create(
        product=product,
        quantity=2,
        unit_price=product.price
    )
    return cart

@pytest.fixture
def order_factory(user):
    def create(**kwargs):
        default = {
            "user": user,
            "shipping_address_line": "123 Test St",
            "shipping_city": "Test City",
            "shipping_postal_code": "12345",
            "shipping_country": "Test Country",
            "payment_method": "chapa",
            "payment_status": Order.PAYMENT_PENDING,
            "status": Order.STATUS_PENDING,
            "total": 100,
        }
        default.update(kwargs)
        return Order.objects.create(**default)
    return create
