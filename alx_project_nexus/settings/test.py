"""
Test settings for alx_project_nexus project.

These settings are used when running tests.
"""
from .base import *
import os

# Override SECRET_KEY for tests if not set in environment
if not os.environ.get("SECRET_KEY"):
    SECRET_KEY = "test-secret-key-for-testing-only"

DEBUG = False

ALLOWED_HOSTS = ["testserver", "localhost"]

# Database - Use test database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "testdb"),
        "USER": os.environ.get("DB_USER", "testuser"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "testpass"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}

# Cache - Use in-memory cache for tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Celery - Run tasks synchronously during tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"

# Email Backend - Use in-memory backend for tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Disable migrations during tests for speed (optional)
# class DisableMigrations:
#     def __contains__(self, item):
#         return True
#     def __getitem__(self, item):
#         return None
# MIGRATION_MODULES = DisableMigrations()

# Password hashers - Use faster hasher for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

