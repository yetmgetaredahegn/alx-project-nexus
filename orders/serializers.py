from decimal import Decimal
from rest_framework import serializers
from .models import Order, OrderItem, OrderCancellationRequest


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "product_id", "product_title", "unit_price", "quantity", "line_total"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "status",
            "payment_status",
            "payment_method",
            "shipping_address_id",
            "total",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "status", "payment_status", "total", "items", "created_at", "updated_at"]


class OrderCreateSerializer(serializers.Serializer):
    shipping_address_id = serializers.UUIDField(required=False, allow_null=True)
    payment_method = serializers.CharField(max_length=64, required=True)

    def validate(self, attrs):
        # additional validation could go here (e.g., payment method whitelist)
        return attrs


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["status"]


class OrderCancellationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderCancellationRequest
        fields = ["id", "order", "user", "reason", "created_at", "handled", "handled_at", "result_note"]
        read_only_fields = ["id", "order", "user", "created_at", "handled", "handled_at", "result_note"]
