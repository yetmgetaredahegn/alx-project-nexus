from django.utils import timezone
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from .models import Notification
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_notification(self, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id)

        send_mail(
            notification.subject,
            notification.message,
            settings.DEFAULT_FROM_EMAIL,
            [notification.user.email],
            fail_silently=False,
        )

        notification.is_sent = True
        notification.sent_at = timezone.now()
        notification.save()

        return {"status": "sent", "id": str(notification.id)}

    except Notification.DoesNotExist:
        # Notification doesn't exist - don't retry, log and return failure
        logger.error(
            f"Notification with id {notification_id} does not exist. "
            "This may indicate a race condition or database inconsistency."
        )
        return {
            "status": "failed",
            "id": str(notification_id),
            "error": "Notification does not exist"
        }
    except Exception as exc:
        # For other exceptions (network, email server, etc.), retry
        logger.warning(
            f"Failed to send notification {notification_id}: {str(exc)}. Retrying..."
        )
        raise self.retry(exc=exc)
