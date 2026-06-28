from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import User
from .permissions import IsAdminOrDirector
from .serializers import UserCreateSerializer, UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsAdminOrDirector()]
        return super().get_permissions()
