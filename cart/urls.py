from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CartItemViewSet, CartViewSet

router = DefaultRouter()
router.register(r"cart/items", CartItemViewSet, basename="cartitem")

urlpatterns = [
    path(
        "cart/",
        CartViewSet.as_view({"get": "list"}),
        name="cart-detail",
    ),
    path(
        "cart/clear/",
        CartViewSet.as_view({"delete": "clear"}),
        name="cart-clear",
    ),
] + router.urls