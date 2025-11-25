from rest_framework import permissions


class IsSellerOrAdmin(permissions.BasePermission):
    """
    Sellers (users in `seller` group) or staff can manage products.
    """

    message = "Only sellers or staff members can modify products."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_staff or request.user.is_superuser:
            return True

        return request.user.groups.filter(name="seller").exists()

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_staff or request.user.is_superuser:
            return True

        return obj.seller_id == request.user.id

