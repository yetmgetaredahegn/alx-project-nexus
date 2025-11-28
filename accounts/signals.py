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
    """
    Signal handler to create profile and send welcome notification when a user is created.
    Uses get_or_create for Profile to handle race conditions safely.
    Wraps notification and email sending in try-except to prevent registration failures.
    """
    if created:
        # Use get_or_create to handle potential race conditions
        # This is safe even if the signal is called multiple times
        profile, profile_created = Profile.objects.get_or_create(user=instance)
        
        if not profile_created:
            logger.warning(
                f"Profile already exists for user {instance.email}. Skipping profile creation."
            )

        # Create notification record - wrap in try-except to prevent registration failure
        note = None
        try:
            note = Notification.objects.create(
                user=instance,
                type=Notification.TYPE_EMAIL,
                subject="Welcome to Nexus",
                message="Your account has been successfully created!",
            )
        except Exception as e:
            # Log the error but don't fail user registration
            logger.error(
                f"Failed to create notification for user {instance.email}: {str(e)}",
                exc_info=True
            )

        # Trigger Celery task - wrap in try-except to prevent registration failure
        # if Celery broker is unavailable
        if note:
            try:
                send_email_notification.delay(str(note.id))
            except Exception as e:
                # Log the error but don't fail user registration
                logger.error(
                    f"Failed to queue email notification for user {instance.email}: {str(e)}",
                    exc_info=True
                )
