import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.test import override_settings
from decimal import Decimal
import uuid

from orders.models import Order
from payments.models import Payment

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
def admin_user(db):
    return User.objects.create_superuser(
        username="admin",
        email="admin@test.com",
        password="pass12345"
    )


@pytest.fixture
def order_factory(user):
    def create(**kwargs):
        default = {
            "user": user,
            "shipping_address_id": uuid.uuid4(),
            "payment_method": "chapa",
            "payment_status": Order.PAYMENT_PENDING,
            "status": Order.STATUS_PENDING,
            "total": Decimal("100.00"),
        }
        default.update(kwargs)
        return Order.objects.create(**default)
    return create


@pytest.fixture
def payment_factory(order_factory):
    def create(**kwargs):
        order = kwargs.pop("order", None)
        if order is None:
            order = order_factory()
        default = {
            "order": order,
            "tx_ref": str(uuid.uuid4()),
            "amount": order.total,
            "currency": "ETB",
            "status": "pending",
        }
        default.update(kwargs)
        return Payment.objects.create(**default)
    return create


@pytest.fixture(autouse=True)
def chapa_settings(settings):
    """Set CHAPA_SECRET_KEY for tests if not already set"""
    if not hasattr(settings, 'CHAPA_SECRET_KEY') or not settings.CHAPA_SECRET_KEY:
        settings.CHAPA_SECRET_KEY = "test_secret_key_for_webhook"
    return settings

