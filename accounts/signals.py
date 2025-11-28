# accounts/signals.py
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Profile
from notifications.models import Notification
from notifications.tasks import send_email_notification

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_profile_and_send_notification(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

        # Create a notification record
        note = Notification.objects.create(
            user=instance,
            type=Notification.TYPE_EMAIL,
            subject="Welcome to Nexus",
            message="Your account has been successfully created!",
        )

        # Trigger Celery task - wrap in try-except to prevent registration failure
        # if Celery broker is unavailable
        try:
            send_email_notification.delay(str(note.id))
        except Exception as e:
            # Log the error but don't fail user registration
            logger.error(
                f"Failed to queue email notification for user {instance.email}: {str(e)}",
                exc_info=True
            )
