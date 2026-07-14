from django.test import TestCase

# Create your tests here.
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from django.contrib.auth import get_user_model
from .models import Choreography, DanceStyle

User = get_user_model()


class VideoPermissionTest(APITestCase):

    def setUp(self):
        self.client_user = User.objects.create_user(
            username="cliente",
            password="123456"
        )

        self.teacher = User.objects.create_user(
            username="profesor",
            password="123456"
        )

        self.style = DanceStyle.objects.create(
            name="Salsa"
        )

        self.choreography = Choreography.objects.create(
            title="Coreografía",
            description="Descripción",
            difficulty_level="beginner",
            thumbnail_url="https://test.com/img.jpg",
            main_teacher=self.teacher,
            dance_style=self.style,
        )

    def test_client_cannot_create_video(self):
        self.client.force_authenticate(self.client_user)

        data = {
            "choreography": str(self.choreography.id),
            "title": "Video 1",
            "video_url": "https://youtube.com/video",
            "sequence_order": 1,
            "duration_seconds": 120,
        }

        response = self.client.post(
            "/api/choreography/videos/",
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )