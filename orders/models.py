from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone


class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_SHIPPED = "shipped"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_SHIPPED, "Shipped"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    PAYMENT_PENDING = "pending"
    PAYMENT_PAID = "paid"
    PAYMENT_FAILED = "failed"

    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_PENDING, "Pending"),
        (PAYMENT_PAID, "Paid"),
        (PAYMENT_FAILED, "Failed"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING)
    payment_status = models.CharField(max_length=32, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_PENDING)
    payment_method = models.CharField(max_length=64, blank=True, null=True)  # snapshot of chosen method (e.g. 'chapa')
    
    # Shipping address fields (user-friendly direct input)
    shipping_address_line = models.CharField(max_length=255, blank=True, null=True)
    shipping_city = models.CharField(max_length=100, blank=True, null=True)
    shipping_postal_code = models.CharField(max_length=20, blank=True, null=True)
    shipping_country = models.CharField(max_length=100, blank=True, null=True)
    
    # Legacy field - kept for backward compatibility but optional now
    shipping_address_id = models.UUIDField(blank=True, null=True)  # snapshot reference to address service
    
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id} - {self.user}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    # keep a snapshot of product details
    product_id = models.IntegerField(null=True, blank=True)  # product PK (catalog.Product) for reference
    product_title = models.CharField(max_length=255)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        # ensure line_total consistent
        self.line_total = (self.unit_price * self.quantity).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_title} x{self.quantity}"


class OrderCancellationRequest(models.Model):
    order = models.ForeignKey(Order, related_name="cancellations", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    handled = models.BooleanField(default=False)
    handled_at = models.DateTimeField(blank=True, null=True)
    result_note = models.TextField(blank=True)

    def mark_handled(self, note: str = ""):
        self.handled = True
        self.handled_at = timezone.now()
        self.result_note = note
        self.save()
