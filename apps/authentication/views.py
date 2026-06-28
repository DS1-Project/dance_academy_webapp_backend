from django.db.models import Q

from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated

from .models import User
from .permissions import INTERNAL_ROLES, IsAdminOrDirector
from .serializers import UserCreateSerializer, UserInternalUpdateSerializer, UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering_fields = ['created_at', 'email', 'role', 'last_name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ('update', 'partial_update'):
            return UserInternalUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ('create', 'list', 'update', 'partial_update'):
            return [IsAdminOrDirector()]
        return super().get_permissions()

    def get_queryset(self):
        qs = User.objects.filter(role__in=INTERNAL_ROLES)

        role = self.request.query_params.get('role')
        if role:
            qs = qs.filter(role=role)

        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')

        is_approved = self.request.query_params.get('is_approved')
        if is_approved is not None:
            qs = qs.filter(is_approved=is_approved.lower() == 'true')

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(email__icontains=search)
                | Q(username__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )

        return qs
