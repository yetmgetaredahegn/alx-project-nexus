from decimal import Decimal
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from cart.models import Cart, CartItem  # assume cart app exists
from catalog.models import Product
from orders.permissions import IsOwnerOrAdmin  # assume catalog app exists
from .models import Order, OrderItem, OrderCancellationRequest
from .serializers import (
    OrderSerializer,
    OrderCreateSerializer,
    OrderItemSerializer,
    OrderStatusUpdateSerializer,
    OrderCancellationSerializer,
)




@extend_schema(tags=["Orders"])
class OrderViewSet(viewsets.ModelViewSet):
    """
    Orders endpoints:
    - list: GET /api/orders/ (current user's orders, paginated)
    - create: POST /api/orders/ (create order from cart)
    - retrieve: GET /api/orders/{id}/
    - partial_update: PATCH /api/orders/{id}/ (for admin to update status)
    - cancel: POST /api/orders/{id}/cancel/
    """
    queryset = Order.objects.all().select_related("user").prefetch_related("items")
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_permissions(self):
        if self.action in ["partial_update"]:
            return [permissions.IsAdminUser()]
        if self.action in ["retrieve"]:
            return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        # list -> only current user's orders (admins can see all if they use admin endpoints)
        queryset = super().get_queryset()
        if self.action == "list" and not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        return queryset

    @extend_schema(
        summary="Create order from current user's cart",
        description="Creates an order from the authenticated user's cart. Validates stock availability, creates order items, decrements product stock, and clears the cart. Returns the created order with payment status 'pending'.",
        request=OrderCreateSerializer,
        responses={201: OrderSerializer, 400: "Bad request (empty cart, insufficient stock, inactive product)", 401: "Unauthorized"},
        tags=["Orders"],
    )
    def create(self, request, *args, **kwargs):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shipping_address_id = serializer.validated_data.get("shipping_address_id")
        payment_method = serializer.validated_data["payment_method"]

        # get cart
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_items = list(cart.items.select_related("product").all())
        if not cart_items:
            return Response({"detail": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        # transaction: validate stock, create order + items, decrement stock, clear cart
        with transaction.atomic():
            # validate stock
            for ci in cart_items:
                product = ci.product
                if not product.is_active:
                    return Response({"detail": f"Product {product.id} is inactive."}, status=status.HTTP_400_BAD_REQUEST)
                if product.stock_quantity < ci.quantity:
                    return Response(
                        {"detail": f"Insufficient stock for product {product.id}."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # create order
            order = Order.objects.create(
                user=request.user,
                payment_method=payment_method,
                payment_status=Order.PAYMENT_PENDING,
                shipping_address_id=shipping_address_id,
                total=Decimal("0.00"),
            )

            total = Decimal("0.00")
            # create items and adjust product stock
            for ci in cart_items:
                product = ci.product
                unit_price = product.price
                quantity = ci.quantity
                line_total = (unit_price * quantity).quantize(Decimal('0.01'))

                OrderItem.objects.create(
                    order=order,
                    product_id=product.pk,
                    product_title=product.title,
                    unit_price=unit_price,
                    quantity=quantity,
                    line_total=line_total,
                )

                # decrement stock (reserve)
                product.stock_quantity -= quantity
                product.save(update_fields=["stock_quantity"])

                total += line_total

            # set total and save
            order.total = total
            order.save(update_fields=["total"])

            # clear cart
            cart.items.all().delete()

            # NOTE: Payment record creation / enqueueing should be done in payments app (or via signal).
            # For now, order.payment_status stays 'pending' and payment_method contains snapshot.

        # return minimal response
        out = OrderSerializer(order, context={"request": request})
        return Response(out.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Update order status (admin only)",
        description="Update the status of an order. Only admin users can update order status. Status changes may trigger notifications.",
        request=OrderStatusUpdateSerializer,
        responses={200: OrderSerializer, 400: "Bad request", 403: "Forbidden (admin only)", 404: "Not found"},
        tags=["Orders"],
    )
    def partial_update(self, request, *args, **kwargs):
        # Only admin allowed (get_permissions covers it)
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # TODO: enqueue notification email/email task on status change (Celery)
        return Response(OrderSerializer(order).data)

    @extend_schema(
        summary="Request order cancellation",
        description="Request cancellation of an order. Only the order owner or admin can request cancellation. Returns a cancellation request record.",
        request=OrderCancellationSerializer,
        responses={200: OrderCancellationSerializer, 400: "Bad request", 403: "Forbidden", 404: "Not found"},
        tags=["Orders"],
    )
    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        order = self.get_object()
        # only owner can request cancellation (or admin on behalf)
        if not (request.user.is_staff or order.user_id == request.user.id):
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

        reason = request.data.get("reason", "")
        cancellation = OrderCancellationRequest.objects.create(order=order, user=request.user, reason=reason)
        # Business rules (refunds, partial cancellations) should be handled in payments app / order handlers.
        return Response(OrderCancellationSerializer(cancellation).data)

