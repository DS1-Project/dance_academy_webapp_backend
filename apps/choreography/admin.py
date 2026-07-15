from django.contrib import admin

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


class VideoClipInline(admin.TabularInline):
    model = VideoClip
    extra = 0


class ChoreographyStatInline(admin.StackedInline):
    model = ChoreographyStat
    extra = 0


@admin.register(DanceStyle)
class DanceStyleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Choreography)
class ChoreographyAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'main_teacher',
        'dance_style',
        'difficulty_level',
        'is_approved',
        'created_at',
    )
    list_filter = ('is_approved', 'difficulty_level', 'dance_style')
    search_fields = ('title', 'main_teacher__email')
    readonly_fields = ('id', 'created_at')
    inlines = [ChoreographyStatInline, VideoClipInline]
    filter_horizontal = ('guest_teachers',)


@admin.register(VideoClip)
class VideoClipAdmin(admin.ModelAdmin):
    list_display = ('title', 'choreography', 'sequence_order', 'duration_seconds')
    list_filter = ('choreography',)
    search_fields = ('title', 'choreography__title')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('client', 'choreography', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('client__email', 'choreography__title')


@admin.register(VideoPlaybackLog)
class VideoPlaybackLogAdmin(admin.ModelAdmin):
    list_display = ('client', 'video_clip', 'created_at')
    list_filter = ('created_at',)


@admin.register(PriceLog)
class PriceLogAdmin(admin.ModelAdmin):
    list_display = ('choreography', 'user', 'old_price', 'new_price', 'registered_at')
    list_filter = ('registered_at',)


@admin.register(RatingLog)
class RatingLogAdmin(admin.ModelAdmin):
    list_display = ('choreography', 'old_rating', 'new_rating', 'action_type', 'registered_at')
    list_filter = ('action_type', 'registered_at')
