from rest_framework.permissions import BasePermission, SAFE_METHODS

from apps.authentication.models import User
from apps.sales.models import Enrollment


class IsTeacher(BasePermission):
    message = 'Solo un profesor aprobado puede realizar esta acción.'

    def has_permission(self, request, view):
        user = request.user
        return (
            user
            and user.is_authenticated
            and user.role == User.Role.TEACHER
            and user.is_approved
            and user.is_active
        )


class IsTeacherOrStaff(BasePermission):
    """Teacher, Admin or Director (approved + active for teacher)."""

    message = 'Solo un profesor, administrador o director puede realizar esta acción.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not user.is_active:
            return False
        if user.role in {User.Role.ADMIN, User.Role.DIRECTOR}:
            return True
        return (
            user.role == User.Role.TEACHER
            and user.is_approved
        )


class IsChoreographyOwnerOrStaff(BasePermission):
    message = 'No tienes permiso para modificar esta coreografía.'

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.role in {User.Role.ADMIN, User.Role.DIRECTOR}:
            return True
        if user.role != User.Role.TEACHER:
            return False
        if obj.main_teacher_id == user.id:
            return True
        return obj.guest_teachers.filter(id=user.id).exists()


class IsEnrolledClientOrStaff(BasePermission):
    """Client must own enrollment; teachers (owners) and staff always allowed."""

    message = 'Debes haber adquirido esta coreografía para acceder a este recurso.'

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        choreography = obj if hasattr(obj, 'main_teacher_id') else getattr(obj, 'choreography', None)
        if choreography is None:
            return False

        if user.role in {User.Role.ADMIN, User.Role.DIRECTOR}:
            return True
        if user.role == User.Role.TEACHER and (
            choreography.main_teacher_id == user.id
            or choreography.guest_teachers.filter(id=user.id).exists()
        ):
            return True
        if user.role == User.Role.CLIENT and user.is_approved and user.is_active:
            return Enrollment.objects.filter(
                client=user,
                choreography=choreography,
            ).exists()
        return False


class IsAdminOrDirector(BasePermission):
    message = 'Solo un Administrador o Director puede realizar esta acción.'

    def has_permission(self, request, view):
        user = request.user
        return (
            user
            and user.is_authenticated
            and user.role in {User.Role.ADMIN, User.Role.DIRECTOR}
        )


class ReadOnlyOrStaffWrite(BasePermission):
    """Anyone authenticated can read; only admin/director can write dance styles."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return user.role in {User.Role.ADMIN, User.Role.DIRECTOR}
