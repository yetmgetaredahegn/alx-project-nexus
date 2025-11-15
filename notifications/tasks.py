from django.utils import timezone
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification


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

    except Exception as exc:
        raise self.retry(exc=exc)
