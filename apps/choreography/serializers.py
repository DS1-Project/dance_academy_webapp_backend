from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from apps.authentication.models import User
from apps.sales.models import Enrollment

from .models import (
    Choreography,
    ChoreographyStat,
    DanceStyle,
    PriceLog,
    RatingLog,
    Review,
    VideoClip,
    VideoPlaybackLog,
)


class DanceStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DanceStyle
        fields = ['id', 'name', 'description']
        read_only_fields = ['id']


class TeacherBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']
        read_only_fields = fields


class ChoreographyStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChoreographyStat
        fields = [
            'actual_price',
            'total_views',
            'total_sales_count',
            'average_rating',
            'last_updated',
        ]
        read_only_fields = fields


class VideoClipPublicSerializer(serializers.ModelSerializer):
    """Metadata without playback URL (catalog / non-enrolled clients)."""

    class Meta:
        model = VideoClip
        fields = [
            'id',
            'title',
            'sequence_order',
            'duration_seconds',
        ]
        read_only_fields = fields


class VideoClipSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoClip
        fields = [
            'id',
            'choreography',
            'title',
            'video_url',
            'sequence_order',
            'duration_seconds',
        ]
        read_only_fields = ['id', 'choreography']


class VideoClipWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoClip
        fields = [
            'title',
            'video_url',
            'sequence_order',
            'duration_seconds',
        ]


class ReviewSerializer(serializers.ModelSerializer):
    client_email = serializers.EmailField(source='client.email', read_only=True)
    client_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id',
            'client',
            'client_email',
            'client_name',
            'choreography',
            'rating',
            'comment',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'client',
            'client_email',
            'client_name',
            'choreography',
            'created_at',
        ]

    def get_client_name(self, obj):
        return f'{obj.client.first_name} {obj.client.last_name}'.strip()


class ReviewCreateSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, attrs):
        client = self.context['request'].user
        choreography = self.context['choreography']

        if not Enrollment.objects.filter(client=client, choreography=choreography).exists():
            raise serializers.ValidationError(
                'Solo puedes calificar coreografías que hayas adquirido.'
            )
        if Review.objects.filter(client=client, choreography=choreography).exists():
            raise serializers.ValidationError(
                'Ya calificaste esta coreografía.'
            )
        return attrs

    def create(self, validated_data):
        client = self.context['request'].user
        choreography = self.context['choreography']
        comment = validated_data.get('comment') or ''

        with transaction.atomic():
            review = Review.objects.create(
                client=client,
                choreography=choreography,
                rating=validated_data['rating'],
                comment=comment,
            )
            RatingLog.objects.create(
                choreography=choreography,
                old_rating=None,
                new_rating=validated_data['rating'],
                action_type='create',
            )
            stats, _ = ChoreographyStat.objects.get_or_create(
                choreography=choreography,
                defaults={'actual_price': Decimal('0.00')},
            )
            stats.update_average_rating()

        return review

    def to_representation(self, instance):
        return ReviewSerializer(instance, context=self.context).data


class ChoreographyListSerializer(serializers.ModelSerializer):
    dance_style = DanceStyleSerializer(read_only=True)
    main_teacher = TeacherBriefSerializer(read_only=True)
    stats = ChoreographyStatSerializer(read_only=True)
    video_count = serializers.SerializerMethodField()

    class Meta:
        model = Choreography
        fields = [
            'id',
            'title',
            'description',
            'difficulty_level',
            'thumbnail_url',
            'is_approved',
            'created_at',
            'main_teacher',
            'dance_style',
            'stats',
            'video_count',
        ]
        read_only_fields = fields

    def get_video_count(self, obj):
        return obj.videos.count()


class ChoreographyDetailSerializer(serializers.ModelSerializer):
    dance_style = DanceStyleSerializer(read_only=True)
    main_teacher = TeacherBriefSerializer(read_only=True)
    guest_teachers = TeacherBriefSerializer(many=True, read_only=True)
    stats = ChoreographyStatSerializer(read_only=True)
    videos = serializers.SerializerMethodField()
    is_purchased = serializers.SerializerMethodField()

    class Meta:
        model = Choreography
        fields = [
            'id',
            'title',
            'description',
            'difficulty_level',
            'thumbnail_url',
            'is_approved',
            'created_at',
            'main_teacher',
            'guest_teachers',
            'dance_style',
            'stats',
            'videos',
            'is_purchased',
        ]
        read_only_fields = fields

    def _can_access_videos(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        user = request.user
        if user.role in {User.Role.ADMIN, User.Role.DIRECTOR}:
            return True
        if user.role == User.Role.TEACHER and (
            obj.main_teacher_id == user.id
            or obj.guest_teachers.filter(id=user.id).exists()
        ):
            return True
        if user.role == User.Role.CLIENT:
            return Enrollment.objects.filter(
                client=user,
                choreography=obj,
            ).exists()
        return False

    def get_videos(self, obj):
        videos = obj.videos.all()
        if self._can_access_videos(obj):
            return VideoClipSerializer(videos, many=True).data
        return VideoClipPublicSerializer(videos, many=True).data

    def get_is_purchased(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        if request.user.role != User.Role.CLIENT:
            return False
        return Enrollment.objects.filter(
            client=request.user,
            choreography=obj,
        ).exists()


class ChoreographyCreateUpdateSerializer(serializers.ModelSerializer):
    actual_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.00'),
        required=False,
        write_only=True,
    )
    guest_teachers = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(
            role=User.Role.TEACHER,
            is_active=True,
            is_approved=True,
        ),
        many=True,
        required=False,
    )
    main_teacher = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(
            role=User.Role.TEACHER,
            is_active=True,
            is_approved=True,
        ),
        required=False,
    )

    class Meta:
        model = Choreography
        fields = [
            'title',
            'description',
            'difficulty_level',
            'thumbnail_url',
            'dance_style',
            'main_teacher',
            'guest_teachers',
            'actual_price',
        ]

    def validate_dance_style(self, value):
        if value is None:
            raise serializers.ValidationError('El estilo de baile es obligatorio.')
        return value

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        actual_price = validated_data.pop('actual_price', Decimal('0.00'))
        guest_teachers = validated_data.pop('guest_teachers', [])

        if user.role == User.Role.TEACHER:
            validated_data['main_teacher'] = user
        elif 'main_teacher' not in validated_data:
            raise serializers.ValidationError(
                {'main_teacher': 'Debes indicar el profesor principal.'}
            )

        validated_data['is_approved'] = False

        with transaction.atomic():
            choreography = Choreography.objects.create(**validated_data)
            if guest_teachers:
                choreography.guest_teachers.set(guest_teachers)
            ChoreographyStat.objects.create(
                choreography=choreography,
                actual_price=actual_price,
            )
            if actual_price is not None:
                PriceLog.objects.create(
                    choreography=choreography,
                    user=user,
                    old_price=Decimal('0.00'),
                    new_price=actual_price,
                )

        return choreography

    def update(self, instance, validated_data):
        request = self.context['request']
        user = request.user
        actual_price = validated_data.pop('actual_price', None)
        guest_teachers = validated_data.pop('guest_teachers', None)

        # Teachers cannot reassign main_teacher or approve via this path
        if user.role == User.Role.TEACHER:
            validated_data.pop('main_teacher', None)

        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if guest_teachers is not None:
                instance.guest_teachers.set(guest_teachers)

            if actual_price is not None:
                stats, _ = ChoreographyStat.objects.get_or_create(
                    choreography=instance,
                    defaults={'actual_price': actual_price},
                )
                old_price = stats.actual_price
                if old_price != actual_price:
                    stats.actual_price = actual_price
                    stats.save(update_fields=['actual_price', 'last_updated'])
                    PriceLog.objects.create(
                        choreography=instance,
                        user=user,
                        old_price=old_price,
                        new_price=actual_price,
                    )

        return instance

    def to_representation(self, instance):
        return ChoreographyDetailSerializer(instance, context=self.context).data


class PriceUpdateSerializer(serializers.Serializer):
    actual_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.00'),
    )

    def save(self, **kwargs):
        choreography = self.context['choreography']
        user = self.context['request'].user
        new_price = self.validated_data['actual_price']

        with transaction.atomic():
            stats, _ = ChoreographyStat.objects.get_or_create(
                choreography=choreography,
                defaults={'actual_price': new_price},
            )
            old_price = stats.actual_price
            stats.actual_price = new_price
            stats.save(update_fields=['actual_price', 'last_updated'])
            PriceLog.objects.create(
                choreography=choreography,
                user=user,
                old_price=old_price,
                new_price=new_price,
            )
        return choreography


class VideoPlaybackLogSerializer(serializers.ModelSerializer):
    video_title = serializers.CharField(source='video_clip.title', read_only=True)
    choreography_id = serializers.UUIDField(
        source='video_clip.choreography_id',
        read_only=True,
    )
    choreography_title = serializers.CharField(
        source='video_clip.choreography.title',
        read_only=True,
    )

    class Meta:
        model = VideoPlaybackLog
        fields = [
            'id',
            'video_clip',
            'video_title',
            'choreography_id',
            'choreography_title',
            'created_at',
        ]
        read_only_fields = fields


class PurchasedChoreographySerializer(serializers.ModelSerializer):
    """Full purchased package with playable video links (HU-13)."""

    dance_style = DanceStyleSerializer(read_only=True)
    main_teacher = TeacherBriefSerializer(read_only=True)
    stats = ChoreographyStatSerializer(read_only=True)
    videos = VideoClipSerializer(many=True, read_only=True)
    acquired_at = serializers.SerializerMethodField()

    class Meta:
        model = Choreography
        fields = [
            'id',
            'title',
            'description',
            'difficulty_level',
            'thumbnail_url',
            'created_at',
            'main_teacher',
            'dance_style',
            'stats',
            'videos',
            'acquired_at',
        ]
        read_only_fields = fields

    def get_acquired_at(self, obj):
        enrollment_map = self.context.get('enrollment_map', {})
        acquired = enrollment_map.get(obj.id)
        return acquired.isoformat() if acquired else None
