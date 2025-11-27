import uuid
import hashlib
from django.db import models
from django.utils import timezone

class Payment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="payment"
    )

    tx_ref = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="ETB")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def mark_completed(self):
        if self.status == "completed":
            return False  # idempotent
        self.status = "completed"
        self.paid_at = timezone.now()
        self.save()
        return True

    def mark_failed(self):
        if self.status == "failed":
            return False
        self.status = "failed"
        self.save()
        return True

    def __str__(self):
        return f"{self.tx_ref} ({self.status})"
