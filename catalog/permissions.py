from rest_framework import permissions


class IsSellerOrAdmin(permissions.BasePermission):
    """
    Sellers (users with is_seller=True) or staff can manage products.
    """

    message = "Only sellers or staff members can modify products."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_staff or request.user.is_superuser:
            return True

        return getattr(request.user, "is_seller", False)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_staff or request.user.is_superuser:
            return True

        # Sellers can only modify their own products
        if getattr(request.user, "is_seller", False):
            return obj.seller_id == request.user.id

        return False


class IsReviewOwnerOrAdmin(permissions.BasePermission):
    """
    Only review owner or admin can update/delete.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_staff or request.user.is_superuser:
            return True

        return obj.user_id == request.user.id
