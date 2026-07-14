from django.db.models import Prefetch, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.authentication.models import User
from apps.sales.models import Enrollment
from apps.sales.permissions import IsClient

from .models import (
    Choreography,
    ChoreographyStat,
    DanceStyle,
    VideoClip,
    VideoPlaybackLog,
)
from .permissions import (
    IsAdminOrDirector,
    IsChoreographyOwnerOrStaff,
    IsTeacherOrStaff,
    ReadOnlyOrStaffWrite,
)
from .serializers import (
    ChoreographyCreateUpdateSerializer,
    ChoreographyDetailSerializer,
    ChoreographyListSerializer,
    DanceStyleSerializer,
    PriceUpdateSerializer,
    PurchasedChoreographySerializer,
    ReviewCreateSerializer,
    ReviewSerializer,
    VideoClipPublicSerializer,
    VideoClipSerializer,
    VideoClipWriteSerializer,
    VideoPlaybackLogSerializer,
)


class DanceStyleViewSet(viewsets.ModelViewSet):
    queryset = DanceStyle.objects.all().order_by('name')
    serializer_class = DanceStyleSerializer
    permission_classes = [IsAuthenticated, ReadOnlyOrStaffWrite]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name']
    ordering = ['name']


class ChoreographyViewSet(viewsets.ModelViewSet):
    queryset = Choreography.objects.all()
    serializer_class = ChoreographyListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'title', 'difficulty_level']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ChoreographyCreateUpdateSerializer
        if self.action == 'retrieve':
            return ChoreographyDetailSerializer
        if self.action == 'purchased':
            return PurchasedChoreographySerializer
        if self.action == 'price':
            return PriceUpdateSerializer
        if self.action == 'videos' and self.request.method == 'POST':
            return VideoClipWriteSerializer
        if self.action == 'videos':
            return VideoClipSerializer
        if self.action == 'reviews' and self.request.method == 'POST':
            return ReviewCreateSerializer
        if self.action == 'reviews':
            return ReviewSerializer
        if self.action == 'playback_history':
            return VideoPlaybackLogSerializer
        return ChoreographyListSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsTeacherOrStaff()]
        if self.action in ('update', 'partial_update', 'destroy', 'price'):
            return [IsAuthenticated(), IsChoreographyOwnerOrStaff()]
        if self.action == 'approve':
            return [IsAdminOrDirector()]
        if self.action in ('purchased', 'playback_history'):
            return [IsClient()]
        if self.action == 'mine':
            return [IsTeacherOrStaff()]
        if self.action == 'videos' and self.request.method == 'POST':
            return [IsAuthenticated(), IsChoreographyOwnerOrStaff()]
        if self.action == 'reviews' and self.request.method == 'POST':
            return [IsClient()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = (
            Choreography.objects.select_related(
                'main_teacher',
                'dance_style',
                'stats',
            )
            .prefetch_related('guest_teachers', 'videos')
        )

        if self.action in (
            'retrieve',
            'update',
            'partial_update',
            'destroy',
            'approve',
            'price',
            'videos',
            'reviews',
        ):
            return qs

        if user.is_superuser or (
            hasattr(user, 'role')
            and user.role in {User.Role.ADMIN, User.Role.DIRECTOR}
        ):
            pass
        elif hasattr(user, 'role') and user.role == User.Role.TEACHER:
            qs = qs.filter(
                Q(is_approved=True)
                | Q(main_teacher=user)
                | Q(guest_teachers=user)
            ).distinct()
        else:
            qs = qs.filter(is_approved=True)

        difficulty = self.request.query_params.get('difficulty_level')
        if difficulty:
            qs = qs.filter(difficulty_level=difficulty)

        dance_style = self.request.query_params.get('dance_style')
        if dance_style:
            qs = qs.filter(dance_style_id=dance_style)

        is_approved = self.request.query_params.get('is_approved')
        if is_approved is not None and (
            user.is_superuser
            or (
                hasattr(user, 'role')
                and user.role in {User.Role.ADMIN, User.Role.DIRECTOR}
            )
        ):
            qs = qs.filter(is_approved=is_approved.lower() == 'true')

        return qs

    def _can_view_unapproved(self, user, choreography):
        if user.is_superuser or user.role in {
            User.Role.ADMIN,
            User.Role.DIRECTOR,
        }:
            return True
        if user.role == User.Role.TEACHER and (
            choreography.main_teacher_id == user.id
            or choreography.guest_teachers.filter(id=user.id).exists()
        ):
            return True
        return False

    def get_object(self):
        obj = super().get_object()
        if self.action in (
            'update',
            'partial_update',
            'destroy',
            'approve',
            'price',
        ) or (
            self.action == 'videos' and self.request.method == 'POST'
        ):
            self.check_object_permissions(self.request, obj)

        if self.action in ('retrieve', 'videos', 'reviews') and not obj.is_approved:
            if not self._can_view_unapproved(self.request.user, obj):
                from rest_framework.exceptions import NotFound
                raise NotFound('No encontrado.')

        return obj

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = ChoreographyDetailSerializer(
            instance,
            context={'request': request},
        )
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        choreography = serializer.save()
        return Response(
            ChoreographyDetailSerializer(
                choreography,
                context={'request': request},
            ).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)
        choreography = serializer.save()
        return Response(
            ChoreographyDetailSerializer(
                choreography,
                context={'request': request},
            ).data,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='mine')
    def mine(self, request):
        user = request.user
        if user.role == User.Role.TEACHER:
            qs = (
                Choreography.objects.filter(
                    Q(main_teacher=user) | Q(guest_teachers=user)
                )
                .distinct()
                .select_related('main_teacher', 'dance_style', 'stats')
                .prefetch_related('videos')
                .order_by('-created_at')
            )
        else:
            qs = self.get_queryset()
        serializer = ChoreographyListSerializer(
            qs,
            many=True,
            context={'request': request},
        )
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='purchased')
    def purchased(self, request):
        enrollments = (
            Enrollment.objects.filter(client=request.user)
            .select_related('choreography')
            .order_by('-acquired_at')
        )
        enrollment_map = {
            e.choreography_id: e.acquired_at for e in enrollments
        }
        choreography_ids = list(enrollment_map.keys())
        choreographies = (
            Choreography.objects.filter(id__in=choreography_ids)
            .select_related('main_teacher', 'dance_style', 'stats')
            .prefetch_related(
                Prefetch(
                    'videos',
                    queryset=VideoClip.objects.order_by('sequence_order'),
                ),
            )
        )
        by_id = {c.id: c for c in choreographies}
        ordered = [by_id[cid] for cid in choreography_ids if cid in by_id]

        serializer = PurchasedChoreographySerializer(
            ordered,
            many=True,
            context={
                'request': request,
                'enrollment_map': enrollment_map,
            },
        )
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='playback-history')
    def playback_history(self, request):
        logs = (
            VideoPlaybackLog.objects.filter(client=request.user)
            .select_related('video_clip', 'video_clip__choreography')
            .order_by('-created_at')
        )
        serializer = VideoPlaybackLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        choreography = self.get_object()
        choreography.is_approved = True
        choreography.save(update_fields=['is_approved'])
        return Response(
            ChoreographyDetailSerializer(
                choreography,
                context={'request': request},
            ).data,
        )

    @action(detail=True, methods=['patch'], url_path='price')
    def price(self, request, pk=None):
        choreography = self.get_object()
        serializer = PriceUpdateSerializer(
            data=request.data,
            context={'request': request, 'choreography': choreography},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        choreography.refresh_from_db()
        return Response(
            ChoreographyDetailSerializer(
                choreography,
                context={'request': request},
            ).data,
        )

    @action(detail=True, methods=['get', 'post'], url_path='videos')
    def videos(self, request, pk=None):
        choreography = self.get_object()

        if request.method == 'GET':
            user = request.user
            can_play = (
                user.role in {User.Role.ADMIN, User.Role.DIRECTOR}
                or (
                    user.role == User.Role.TEACHER
                    and (
                        choreography.main_teacher_id == user.id
                        or choreography.guest_teachers.filter(id=user.id).exists()
                    )
                )
                or (
                    user.role == User.Role.CLIENT
                    and Enrollment.objects.filter(
                        client=user,
                        choreography=choreography,
                    ).exists()
                )
            )
            videos = choreography.videos.all()
            if can_play:
                data = VideoClipSerializer(videos, many=True).data
            else:
                data = VideoClipPublicSerializer(videos, many=True).data
            return Response(data)

        write_serializer = VideoClipWriteSerializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        video = VideoClip.objects.create(
            choreography=choreography,
            **write_serializer.validated_data,
        )
        return Response(
            VideoClipSerializer(video).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['get', 'post'], url_path='reviews')
    def reviews(self, request, pk=None):
        choreography = self.get_object()

        if request.method == 'GET':
            reviews = choreography.reviews.select_related('client').all()
            return Response(ReviewSerializer(reviews, many=True).data)

        serializer = ReviewCreateSerializer(
            data=request.data,
            context={'request': request, 'choreography': choreography},
        )
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response(
            ReviewSerializer(review).data,
            status=status.HTTP_201_CREATED,
        )


class VideoClipViewSet(viewsets.ModelViewSet):
    queryset = VideoClip.objects.select_related('choreography').all()
    serializer_class = VideoClipSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch', 'put', 'delete', 'post', 'head', 'options']

    def get_serializer_class(self):
        if self.action in ('update', 'partial_update'):
            return VideoClipWriteSerializer
        return VideoClipSerializer

    def get_permissions(self):
        if self.action in ('update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsChoreographyOwnerOrStaff()]
        if self.action == 'play':
            return [IsClient()]
        return [IsAuthenticated()]

    def get_object(self):
        obj = super().get_object()
        if self.action in ('update', 'partial_update', 'destroy'):
            self.check_object_permissions(self.request, obj.choreography)
        return obj

    def list(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Usa GET /api/choreographies/{id}/videos/.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def create(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Usa POST /api/choreographies/{id}/videos/.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def retrieve(self, request, *args, **kwargs):
        video = self.get_object()
        choreography = video.choreography
        user = request.user
        can_play = (
            user.role in {User.Role.ADMIN, User.Role.DIRECTOR}
            or (
                user.role == User.Role.TEACHER
                and (
                    choreography.main_teacher_id == user.id
                    or choreography.guest_teachers.filter(id=user.id).exists()
                )
            )
            or (
                user.role == User.Role.CLIENT
                and Enrollment.objects.filter(
                    client=user,
                    choreography=choreography,
                ).exists()
            )
        )
        if can_play:
            return Response(VideoClipSerializer(video).data)
        return Response(VideoClipPublicSerializer(video).data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        video = self.get_object()
        serializer = VideoClipWriteSerializer(
            video,
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(VideoClipSerializer(video).data)

    def destroy(self, request, *args, **kwargs):
        video = self.get_object()
        video.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='play')
    def play(self, request, pk=None):
        video = self.get_object()
        choreography = video.choreography

        if not Enrollment.objects.filter(
            client=request.user,
            choreography=choreography,
        ).exists():
            return Response(
                {'detail': 'Debes haber adquirido esta coreografía para reproducirla.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        log = VideoPlaybackLog.objects.create(
            client=request.user,
            video_clip=video,
        )
        stats, _ = ChoreographyStat.objects.get_or_create(
            choreography=choreography,
            defaults={'actual_price': 0},
        )
        stats.total_views += 1
        stats.save(update_fields=['total_views', 'last_updated'])

        return Response(
            VideoPlaybackLogSerializer(log).data,
            status=status.HTTP_201_CREATED,
        )
