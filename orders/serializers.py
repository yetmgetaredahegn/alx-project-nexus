from decimal import Decimal
from rest_framework import serializers
from .models import Order, OrderItem, OrderCancellationRequest


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "product_id", "product_title", "unit_price", "quantity", "line_total"]


class ShippingAddressSerializer(serializers.Serializer):
    """User-friendly shipping address input"""
    address_line = serializers.CharField(max_length=255, required=True)
    city = serializers.CharField(max_length=100, required=True)
    postal_code = serializers.CharField(max_length=20, required=True)
    country = serializers.CharField(max_length=100, required=True)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shipping_address = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "status",
            "payment_status",
            "payment_method",
            "shipping_address",
            "shipping_address_id",  # Keep for backward compatibility
            "total",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "status", "payment_status", "total", "items", "created_at", "updated_at"]

    def get_shipping_address(self, obj):
        """Return shipping address as a user-friendly object"""
        if obj.shipping_address_line:
            return {
                "address_line": obj.shipping_address_line,
                "city": obj.shipping_city,
                "postal_code": obj.shipping_postal_code,
                "country": obj.shipping_country,
            }
        return None


class OrderCreateSerializer(serializers.Serializer):
    """User-friendly order creation - accepts shipping address as object"""
    shipping_address = ShippingAddressSerializer(required=True)
    payment_method = serializers.CharField(max_length=64, required=True)
    
    # Legacy field - kept for backward compatibility but deprecated
    shipping_address_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        # Validate payment method
        valid_methods = ["chapa", "cash_on_delivery", "bank_transfer"]
        payment_method = attrs.get("payment_method", "").lower()
        if payment_method not in valid_methods:
            raise serializers.ValidationError(
                f"Invalid payment method. Must be one of: {', '.join(valid_methods)}"
            )
        
        # If both shipping_address and shipping_address_id are provided, prefer shipping_address
        if attrs.get("shipping_address") and attrs.get("shipping_address_id"):
            # Remove shipping_address_id if shipping_address is provided
            attrs.pop("shipping_address_id", None)
        
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
