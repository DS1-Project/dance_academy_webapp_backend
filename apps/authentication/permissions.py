from rest_framework.permissions import BasePermission

from .models import User

INTERNAL_ROLES = frozenset({
    User.Role.ADMIN,
    User.Role.DIRECTOR,
    User.Role.TEACHER,
})

INTERNAL_ROLE_CHOICES = [
    choice for choice in User.Role.choices if choice[0] != User.Role.CLIENT
]


class IsAdminOrDirector(BasePermission):
    message = 'Solo un Administrador o Director puede realizar esta acción.'

    def has_permission(self, request, view):
        user = request.user
        return (
            user
            and user.is_authenticated
            and user.role in {User.Role.ADMIN, User.Role.DIRECTOR}
        )
