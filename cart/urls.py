from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import CartViewSet, CartItemViewSet

router = DefaultRouter()
router.register(r"cart/items", CartItemViewSet, basename="cart-item")
# Register a top-level route for cart; ViewSet.list -> GET /cart/
router.register(r"cart", CartViewSet, basename="cart")

urlpatterns = router.urls