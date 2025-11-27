from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id", "order", "tx_ref", "amount", "currency",
            "status", "created_at", "paid_at"
        ]
        read_only_fields = fields
