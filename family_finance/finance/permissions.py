from rest_framework.permissions import BasePermission, SAFE_METHODS

from finance.models import User


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and getattr(request.user, 'role', None) == User.ROLE_ADMIN
        )


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return getattr(request.user, 'role', None) == User.ROLE_ADMIN


class IsExpenseOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if getattr(request.user, 'role', None) == User.ROLE_ADMIN:
            return True
        return obj.user_id == request.user.id
