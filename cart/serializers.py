from django.db import transaction
from rest_framework import serializers

from catalog.models import Product
from .models import Cart, CartItem


class ProductSummarySerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "title", "price"]

    def get_price(self, obj):
        return str(obj.price)


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSummarySerializer(read_only=True)
    line_total = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",
            "quantity",
            "unit_price",
            "line_total",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["unit_price", "line_total", "created_at", "updated_at"]

    def get_line_total(self, obj):
        return str(obj.line_total)

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value


class CartItemCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(default=1)

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be > 0")
        return value

    def validate_product_id(self, value):
        try:
            product = Product.objects.get(pk=value, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or inactive.")
        return value

    def save(self, **kwargs):
        """
        Create or increment CartItem. Expects 'cart' in context (Cart instance).
        """
        cart: Cart = self.context["cart"]
        product = Product.objects.select_for_update().get(pk=self.validated_data["product_id"])
        qty = self.validated_data["quantity"]

        # Validate stock availability (product has stock_quantity field)
        if hasattr(product, "stock_quantity") and product.stock_quantity < qty:
            raise serializers.ValidationError("Not enough stock for this product.")

        # Upsert item
        with transaction.atomic():
            item, created = CartItem.objects.select_for_update().get_or_create(
                cart=cart, product=product,
                defaults={"quantity": qty, "unit_price": product.price}
            )
            if not created:
                item.quantity += qty
                item.save(update_fields=["quantity", "updated_at"])
        return item


class CartItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["quantity"]
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return value

    def update(self, instance, validated_data):
        qty = validated_data["quantity"]
        # check product stock
        product = instance.product
        if hasattr(product, "stock_quantity") and product.stock_quantity < qty:
            raise serializers.ValidationError("Not enough stock for this product.")
        instance.quantity = qty
        instance.save(update_fields=["quantity", "updated_at"])
        return instance


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "items", "total", "created_at", "updated_at"]

    def get_total(self, obj):
        return str(obj.total)
