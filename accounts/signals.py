# accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Profile
from notifications.models import Notification
from notifications.tasks import send_email_notification


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

        # Trigger Celery
        send_email_notification.delay(str(note.id))
