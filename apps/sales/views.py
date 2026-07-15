from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.authentication.models import User

from .models import Enrollment, Sale
from .permissions import IsAdminOrDirectorOrReadOwn, IsClient, IsSaleOwnerOrAdmin
from .serializers import (
    CheckoutSerializer,
    EnrollmentSerializer,
    SaleCreateSerializer,
    SaleSerializer,
)


class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at', 'total_amount', 'payment_status']
    ordering = ['-created_at']
    http_method_names = ['get', 'post', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'create':
            return SaleCreateSerializer
        if self.action == 'checkout':
            return CheckoutSerializer
        if self.action == 'my_enrollments':
            return EnrollmentSerializer
        return SaleSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsClient()]
        if self.action in ('list', 'retrieve'):
            return [IsAdminOrDirectorOrReadOwn()]
        if self.action == 'checkout':
            return [IsAuthenticated(), IsSaleOwnerOrAdmin()]
        if self.action == 'my_enrollments':
            return [IsClient()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        qs = Sale.objects.select_related('client').prefetch_related(
            'details__choreography'
        )

        if user.is_superuser or (
            hasattr(user, 'role')
            and user.role in {User.Role.ADMIN, User.Role.DIRECTOR}
        ):
            return qs

        return qs.filter(client=user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sale = serializer.save()
        return Response(
            SaleSerializer(sale, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        serializer = SaleSerializer(instance, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='checkout')
    def checkout(self, request, pk=None):
        sale = self.get_object()
        self.check_object_permissions(request, sale)
        serializer = CheckoutSerializer(
            data=request.data,
            context={'request': request, 'sale': sale},
        )
        serializer.is_valid(raise_exception=True)
        updated_sale = serializer.save()
        return Response(
            SaleSerializer(updated_sale, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['get'], url_path='my-enrollments')
    def my_enrollments(self, request):
        enrollments = (
            Enrollment.objects.filter(client=request.user)
            .select_related('choreography')
            .order_by('-acquired_at')
        )
        serializer = EnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)
