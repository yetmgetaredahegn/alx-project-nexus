# notifications/models.py
import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings


class Notification(models.Model):
    """
    Stores all notification events (email, SMS, push).
    Helps with debugging, resending, logs & audit trails.
    """
    TYPE_EMAIL = "email"
    TYPE_SMS = "sms"
    TYPE_PUSH = "push"

    TYPE_CHOICES = [
        (TYPE_EMAIL, "Email"),
        (TYPE_SMS, "SMS"),
        (TYPE_PUSH, "Push Notification"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Target user (optional for system notifications)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )

    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_EMAIL)
    subject = models.CharField(max_length=255, null=True, blank=True)
    message = models.TextField(null=True, blank=True)

    # Track delivery status
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.type.upper()} -> {self.user.email if self.user else 'SYSTEM'}"
