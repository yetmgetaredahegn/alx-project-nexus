import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_project_nexus.settings')

celery = Celery('alx_project_nexus')
celery.config_from_object('django.conf:settings',namespace='CELERY')

celery.autodiscover_tasks()