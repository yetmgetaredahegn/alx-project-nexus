"""
Pytest configuration and fixtures for catalog app tests.
"""
import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def clear_cache():
    """Automatically clear cache before each test to ensure test isolation"""
    cache.clear()
    yield
    # Optionally clear cache after test as well
    cache.clear()

