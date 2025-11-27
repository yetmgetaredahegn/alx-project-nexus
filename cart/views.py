from django.db import transaction
from rest_framework import status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from rest_framework import serializers

from .models import Cart, CartItem
from .serializers import (
    CartSerializer,
    CartItemSerializer,
    CartItemCreateSerializer,
    CartItemUpdateSerializer,
)


def get_or_create_cart_for_user(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


class CartViewSet(viewsets.ViewSet):
    """
    GET /api/cart/ -> retrieve current user's cart
    DELETE /api/cart/clear/ -> clear current user's cart
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get current user's cart",
        description="Returns the authenticated user's active cart including items and total price.",
        responses={200: CartSerializer},
        tags=["Cart"],
    )
    def list(self, request):
        # list() mapped to GET /cart/ by DefaultRouter when using ViewSet
        cart = get_or_create_cart_for_user(request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @extend_schema(
        summary="Clear cart",
        description="Delete all items from the authenticated user's cart.",
        responses={204: OpenApiResponse(description="Cart cleared")},
        tags=["Cart"],
    )
    @action(detail=False, methods=["delete"], url_path="clear")
    def clear(self, request):
        cart = get_or_create_cart_for_user(request.user)
        cart.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartItemViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [IsAuthenticated]
    serializer_class = CartItemSerializer
    lookup_field = "pk"

    def get_queryset(self):
        cart = get_or_create_cart_for_user(self.request.user)
        return CartItem.objects.filter(cart=cart).select_related("product")

    @extend_schema(
        summary="List cart items",
        description="Lists all items inside the authenticated user's cart.",
        responses={200: CartItemSerializer(many=True)},
        tags=["Cart"],
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = CartItemSerializer(queryset, many=True)
        return Response({"results": serializer.data})

    @extend_schema(
        summary="Add item to cart",
        description=(
            "Adds an item to the user's cart. If the product already exists in the cart, "
            "its quantity will be incremented instead of creating a new item."
        ),
        request=CartItemCreateSerializer,
        responses={201: CartItemSerializer},
        tags=["Cart"],
    )
    def create(self, request, *args, **kwargs):
        cart = get_or_create_cart_for_user(request.user)
        serializer = CartItemCreateSerializer(data=request.data, context={"cart": cart})
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            item = serializer.save()

        return Response(CartItemSerializer(item).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Update cart item quantity",
        description="Updates the quantity of an existing cart item.",
        request=CartItemUpdateSerializer,
        responses={200: CartItemSerializer},
        tags=["Cart"],
    )
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = CartItemUpdateSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(CartItemSerializer(instance).data)

    @extend_schema(
        summary="Delete cart item",
        description="Removes an item from the user's cart.",
        responses={204: OpenApiResponse(description="Item removed")},
        tags=["Cart"],
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
