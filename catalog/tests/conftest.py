"""
Shared pytest fixtures for catalog app tests.
"""
import itertools

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

from catalog.models import Category, Product, Review

User = get_user_model()


class FactoryHelper:
    """Simple helper to provide call + create_batch behaviour."""

    def __init__(self, creator):
        self._creator = creator

    def __call__(self, **kwargs):
        return self._creator(**kwargs)

    def create_batch(self, size, **kwargs):
        return [self._creator(**kwargs) for _ in range(size)]


@pytest.fixture
def user_factory(db):
    counter = itertools.count(1)

    def create_user(**kwargs):
        idx = next(counter)
        defaults = {
            "username": kwargs.get("username", f"user{idx}"),
            "email": kwargs.get("email", f"user{idx}@example.com"),
            "password": kwargs.get("password", "password123"),
        }
        defaults.update(kwargs)
        password = defaults.pop("password")
        return User.objects.create_user(password=password, **defaults)

    return create_user


@pytest.fixture
def user(user_factory):
    return user_factory()


@pytest.fixture
def seller_user(user_factory):
    seller = user_factory(username="seller1", email="seller1@example.com")
    seller.is_seller = True
    seller.save(update_fields=["is_seller"])
    return seller


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="password123",
    )


@pytest.fixture
def category_factory(db):
    counter = itertools.count(1)

    def create_category(**kwargs):
        idx = next(counter)
        defaults = {"name": kwargs.get("name", f"Category {idx}")}
        defaults.update(kwargs)
        return Category.objects.create(**defaults)

    return FactoryHelper(create_category)


@pytest.fixture
def product_factory(db, category_factory, seller_user):
    counter = itertools.count(1)

    def create_product(**kwargs):
        idx = next(counter)
        category = kwargs.pop("category", category_factory())
        seller = kwargs.pop("seller", seller_user)
        defaults = {
            "title": kwargs.get("title", f"Product {idx}"),
            "description": kwargs.get("description", "Test Description"),
            "price": kwargs.get("price", 10.99),
            "stock_quantity": kwargs.get("stock_quantity", 5),
            "category": category,
            "seller": seller,
        }
        defaults.update(kwargs)
        return Product.objects.create(**defaults)

    return FactoryHelper(create_product)


@pytest.fixture
def review_factory(db, product_factory, user_factory):
    counter = itertools.count(1)

    def create_review(**kwargs):
        idx = next(counter)
        product = kwargs.pop("product", product_factory())
        reviewer = kwargs.pop("user", user_factory())
        defaults = {
            "rating": kwargs.get("rating", ((idx - 1) % 5) + 1),
            "comment": kwargs.get("comment", f"Review {idx}"),
            "product": product,
            "user": reviewer,
        }
        defaults.update(kwargs)
        return Review.objects.create(**defaults)

    return FactoryHelper(create_review)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture(autouse=True)
def clear_cache():
    """Automatically clear cache before each test to ensure test isolation."""
    cache.clear()
    yield
    cache.clear()

