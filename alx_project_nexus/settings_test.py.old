from .settings import *
import os

# Override SECRET_KEY for tests if not set in environment
if not os.environ.get("SECRET_KEY"):
    SECRET_KEY = "test-secret-key-for-testing-only"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "testdb"),
        "USER": os.environ.get("DB_USER", "testuser"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "testpass"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", 5432),
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Override cache to in-memory
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
