from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import User
from apps.choreography.models import (
    Choreography,
    ChoreographyStat,
    DanceStyle,
    Review,
    VideoClip,
    VideoPlaybackLog,
)
from apps.sales.models import Enrollment


class ChoreographyAPITestCase(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin.user',
            email='admin@test.com',
            password='AdminPass123',
            first_name='Admin',
            last_name='User',
            role=User.Role.ADMIN,
            is_approved=True,
        )
        self.teacher = User.objects.create_user(
            username='teacher.user',
            email='teacher@test.com',
            password='TeacherPass123',
            first_name='Teacher',
            last_name='User',
            role=User.Role.TEACHER,
            is_approved=True,
        )
        self.other_teacher = User.objects.create_user(
            username='other.teacher',
            email='other.teacher@test.com',
            password='TeacherPass123',
            first_name='Other',
            last_name='Teacher',
            role=User.Role.TEACHER,
            is_approved=True,
        )
        self.client_user = User.objects.create_user(
            username='client.user',
            email='client@test.com',
            password='ClientPass123',
            first_name='Client',
            last_name='User',
            role=User.Role.CLIENT,
            is_approved=True,
        )
        self.style = DanceStyle.objects.create(
            name='Salsa',
            description='Ritmo salsa',
        )
        self.choreography = Choreography.objects.create(
            title='Salsa Básica',
            description='Introducción a salsa',
            difficulty_level=Choreography.Difficulty.BEGINNER,
            thumbnail_url='https://example.com/thumb.jpg',
            is_approved=True,
            main_teacher=self.teacher,
            dance_style=self.style,
        )
        ChoreographyStat.objects.create(
            choreography=self.choreography,
            actual_price=Decimal('29.99'),
        )
        self.video = VideoClip.objects.create(
            choreography=self.choreography,
            title='Clip 1',
            video_url='https://example.com/video1.mp4',
            sequence_order=1,
            duration_seconds=120,
        )
        self.draft = Choreography.objects.create(
            title='Borrador Bachata',
            description='Sin aprobar',
            difficulty_level=Choreography.Difficulty.INTERMEDIATE,
            thumbnail_url='https://example.com/draft.jpg',
            is_approved=False,
            main_teacher=self.teacher,
            dance_style=self.style,
        )
        ChoreographyStat.objects.create(
            choreography=self.draft,
            actual_price=Decimal('19.99'),
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)


class DanceStyleTests(ChoreographyAPITestCase):
    def test_authenticated_user_can_list_styles(self):
        self.authenticate(self.client_user)
        response = self.client.get(reverse('dance-styles-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_client_cannot_create_style(self):
        self.authenticate(self.client_user)
        response = self.client.post(
            reverse('dance-styles-list'),
            {'name': 'Bachata', 'description': 'Ritmo'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_style(self):
        self.authenticate(self.admin)
        response = self.client.post(
            reverse('dance-styles-list'),
            {'name': 'Bachata', 'description': 'Ritmo bachata'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Bachata')


class CatalogAndTeacherTests(ChoreographyAPITestCase):
    def test_client_lists_only_approved(self):
        self.authenticate(self.client_user)
        response = self.client.get(reverse('choreographies-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [item['title'] for item in response.data]
        self.assertIn('Salsa Básica', titles)
        self.assertNotIn('Borrador Bachata', titles)

    def test_client_cannot_see_video_url_without_purchase(self):
        self.authenticate(self.client_user)
        response = self.client.get(
            reverse('choreographies-detail', args=[self.choreography.id]),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_purchased'])
        self.assertEqual(len(response.data['videos']), 1)
        self.assertNotIn('video_url', response.data['videos'][0])

    def test_teacher_can_create_choreography_with_price(self):
        self.authenticate(self.teacher)
        response = self.client.post(
            reverse('choreographies-list'),
            {
                'title': 'Nueva Coreo',
                'description': 'Descripción',
                'difficulty_level': 'advanced',
                'thumbnail_url': 'https://example.com/new.jpg',
                'dance_style': str(self.style.id),
                'actual_price': '45.50',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['is_approved'])
        self.assertEqual(
            Decimal(response.data['stats']['actual_price']),
            Decimal('45.50'),
        )
        self.assertEqual(
            str(response.data['main_teacher']['id']),
            str(self.teacher.id),
        )

    def test_teacher_can_add_video(self):
        self.authenticate(self.teacher)
        response = self.client.post(
            reverse('choreographies-videos', args=[self.choreography.id]),
            {
                'title': 'Clip 2',
                'video_url': 'https://example.com/video2.mp4',
                'sequence_order': 2,
                'duration_seconds': 90,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Clip 2')
        self.assertEqual(self.choreography.videos.count(), 2)

    def test_other_teacher_cannot_add_video(self):
        self.authenticate(self.other_teacher)
        response = self.client.post(
            reverse('choreographies-videos', args=[self.choreography.id]),
            {
                'title': 'Hack',
                'video_url': 'https://example.com/hack.mp4',
                'sequence_order': 9,
                'duration_seconds': 10,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_approve(self):
        self.authenticate(self.admin)
        response = self.client.post(
            reverse('choreographies-approve', args=[self.draft.id]),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.draft.refresh_from_db()
        self.assertTrue(self.draft.is_approved)

    def test_teacher_can_update_price(self):
        self.authenticate(self.teacher)
        response = self.client.patch(
            reverse('choreographies-price', args=[self.choreography.id]),
            {'actual_price': '35.00'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Decimal(response.data['stats']['actual_price']),
            Decimal('35.00'),
        )

    def test_mine_returns_teacher_uploads(self):
        self.authenticate(self.teacher)
        response = self.client.get(reverse('choreographies-mine'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [item['title'] for item in response.data]
        self.assertIn('Salsa Básica', titles)
        self.assertIn('Borrador Bachata', titles)


class PurchasedAndHistoryTests(ChoreographyAPITestCase):
    def setUp(self):
        super().setUp()
        Enrollment.objects.create(
            client=self.client_user,
            choreography=self.choreography,
        )

    def test_purchased_includes_video_urls(self):
        self.authenticate(self.client_user)
        response = self.client.get(reverse('choreographies-purchased'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Salsa Básica')
        self.assertIn('video_url', response.data[0]['videos'][0])
        self.assertIsNotNone(response.data[0]['acquired_at'])

    def test_detail_shows_videos_when_purchased(self):
        self.authenticate(self.client_user)
        response = self.client.get(
            reverse('choreographies-detail', args=[self.choreography.id]),
        )
        self.assertTrue(response.data['is_purchased'])
        self.assertIn('video_url', response.data['videos'][0])

    def test_client_can_log_playback_and_see_history(self):
        self.authenticate(self.client_user)
        play = self.client.post(
            reverse('videos-play', args=[self.video.id]),
        )
        self.assertEqual(play.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VideoPlaybackLog.objects.count(), 1)

        history = self.client.get(reverse('choreographies-playback-history'))
        self.assertEqual(history.status_code, status.HTTP_200_OK)
        self.assertEqual(len(history.data), 1)
        self.assertEqual(history.data[0]['video_title'], 'Clip 1')

    def test_non_enrolled_client_cannot_play(self):
        other = User.objects.create_user(
            username='other.client',
            email='other@test.com',
            password='ClientPass123',
            role=User.Role.CLIENT,
            is_approved=True,
        )
        self.authenticate(other)
        response = self.client.post(reverse('videos-play', args=[self.video.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_enrolled_client_can_review(self):
        self.authenticate(self.client_user)
        response = self.client.post(
            reverse('choreographies-reviews', args=[self.choreography.id]),
            {'rating': 5, 'comment': 'Excelente'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 1)
        self.choreography.stats.refresh_from_db()
        self.assertEqual(
            Decimal(self.choreography.stats.average_rating),
            Decimal('5.00'),
        )

    def test_duplicate_review_rejected(self):
        self.authenticate(self.client_user)
        self.client.post(
            reverse('choreographies-reviews', args=[self.choreography.id]),
            {'rating': 4},
            format='json',
        )
        response = self.client.post(
            reverse('choreographies-reviews', args=[self.choreography.id]),
            {'rating': 3},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class MediaUploadTests(ChoreographyAPITestCase):
    def test_teacher_can_upload_video_file(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.authenticate(self.teacher)
        upload = SimpleUploadedFile(
            'clip.mp4',
            b'fake-video-bytes',
            content_type='video/mp4',
        )
        response = self.client.post(
            reverse('media-upload'),
            {'file': upload},
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('url', response.data)
        self.assertIn('/media/', response.data['url'])

    def test_upload_rejects_missing_file(self):
        self.authenticate(self.teacher)
        response = self.client.post(reverse('media-upload'), {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_rejects_non_media_content_type(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.authenticate(self.teacher)
        upload = SimpleUploadedFile(
            'notes.txt',
            b'hello',
            content_type='text/plain',
        )
        response = self.client.post(
            reverse('media-upload'),
            {'file': upload},
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SeedCatalogDemoTests(ChoreographyAPITestCase):
    def test_seed_command_creates_five_teachers_with_videos(self):
        from django.core.management import call_command

        call_command('seed_catalog_demo', password='TeacherPass123')

        emails = [t['email'] for t in __import__(
            'apps.choreography.management.commands.seed_catalog_demo',
            fromlist=['TEACHERS'],
        ).TEACHERS]
        teachers = User.objects.filter(email__in=emails, role=User.Role.TEACHER)
        self.assertEqual(teachers.count(), 5)

        for teacher in teachers:
            choreos = Choreography.objects.filter(main_teacher=teacher, is_approved=True)
            self.assertGreaterEqual(choreos.count(), 2)
            self.assertLessEqual(choreos.count(), 10)
            for choreo in choreos:
                video_count = choreo.videos.count()
                self.assertGreaterEqual(video_count, 1)
                self.assertLessEqual(video_count, 20)

        style_names = ['Salsa', 'Bachata', 'Merengue', 'Hip-Hop', 'Reggaetón']
        self.assertEqual(
            DanceStyle.objects.filter(name__in=style_names).count(),
            5,
        )

    def test_anonymous_can_list_dance_styles(self):
        response = self.client.get(reverse('dance-styles-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
