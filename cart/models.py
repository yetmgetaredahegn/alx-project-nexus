from decimal import Decimal
from django.conf import settings
from django.db import models
from django.db.models import F, Sum


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def items_qs(self):
        return self.items.select_related("product")

    @property
    def total(self) -> Decimal:
        agg = self.items.aggregate(total=Sum(F("unit_price") * F("quantity")))
        return agg["total"] or Decimal("0.00")

    def __str__(self):
        return f"Cart({self.user})"


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart, related_name="items", on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        "catalog.Product",
        related_name="cart_items",
        on_delete=models.PROTECT,
    )
    quantity = models.PositiveIntegerField(default=1)
    # snapshot of product price at the time of add
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("cart", "product")

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.product} x {self.quantity}"
