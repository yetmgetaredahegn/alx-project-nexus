"""
Pytest configuration and fixtures for catalog app tests.
"""
import pytest
from django.core.cache import cache
from rest_framework.test import APIClient
import pytest
from catalog.models import Category, Product, Review
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="user1",
        email="user1@example.com",
        password="password123"
    )


@pytest.fixture
def seller_user(db):
    return User.objects.create_user(
        username="seller1",
        email="seller1@example.com",
        password="password123",
    )


@pytest.fixture
def category_factory(db):
    def create_category(**kwargs):
        defaults = {"name": "Category 1"}
        defaults.update(kwargs)
        return Category.objects.create(**defaults)
    return create_category


@pytest.fixture
def product_factory(db, category_factory, seller_user):
    def create_product(**kwargs):
        category = kwargs.pop("category", category_factory())
        defaults = {
            "name": "Test Product",
            "description": "Test Description",
            "price": 10.99,
            "category": category,
            "seller": seller_user,
        }
        defaults.update(kwargs)
        return Product.objects.create(**defaults)
    return create_product


@pytest.fixture
def review_factory(db, product_factory, user):
    def create_review(**kwargs):
        product = kwargs.pop("product", product_factory())
        reviewer = kwargs.pop("user", user)
        defaults = {
            "rating": 4,
            "comment": "Good product",
            "product": product,
            "user": reviewer,
        }
        defaults.update(kwargs)
        return Review.objects.create(**defaults)
    return create_review


@pytest.fixture
def api_client():
    return APIClient()



@pytest.fixture(autouse=True)
def clear_cache():
    """Automatically clear cache before each test to ensure test isolation"""
    cache.clear()
    yield
    # Optionally clear cache after test as well
    cache.clear()

