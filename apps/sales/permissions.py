from rest_framework.permissions import BasePermission

from apps.authentication.models import User
from apps.authentication.permissions import IsAdminOrDirector


class IsClient(BasePermission):
    message = 'Solo un cliente puede realizar esta acción.'

    def has_permission(self, request, view):
        user = request.user
        return (
            user
            and user.is_authenticated
            and user.role == User.Role.CLIENT
            and user.is_approved
            and user.is_active
        )


class IsSaleOwnerOrAdmin(BasePermission):
    message = 'No tienes permiso para acceder a esta venta.'

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.role in {User.Role.ADMIN, User.Role.DIRECTOR}:
            return True
        return obj.client_id == user.id


class IsAdminOrDirectorOrReadOwn(BasePermission):
    """Admin/Director: full list access. Client: own sales only (enforced in queryset)."""

    message = 'No tienes permiso para listar ventas.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.role in {User.Role.ADMIN, User.Role.DIRECTOR}:
            return True
        return (
            user.role == User.Role.CLIENT
            and user.is_approved
            and user.is_active
        )


# Re-export for convenience in views
__all__ = [
    'IsAdminOrDirector',
    'IsClient',
    'IsSaleOwnerOrAdmin',
    'IsAdminOrDirectorOrReadOwn',
]
