from .settings import *  

# -------------------------------
# Test DB (can use same as CI)
# -------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'testdb'),
        'USER': os.environ.get('DB_USER', 'testuser'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'testpass'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', 5432),
    }
}

# -------------------------------
# Celery - run tasks synchronously in tests
# -------------------------------
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
