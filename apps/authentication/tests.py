from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import User


class AuthenticationAPITestCase(APITestCase):
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
        self.client_user = User.objects.create_user(
            username='client.user',
            email='client@test.com',
            password='ClientPass123',
            first_name='Client',
            last_name='User',
            role=User.Role.CLIENT,
            is_approved=True,
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)


class UserModelSerializerTests(AuthenticationAPITestCase):
    def test_user_model_persists_expected_fields(self):
        user = User.objects.get(email='admin@test.com')
        self.assertEqual(user.role, User.Role.ADMIN)
        self.assertTrue(user.is_approved)
        self.assertIsNotNone(user.created_at)
        self.assertEqual(user._meta.db_table, 'auth_user')


class HU01CreateInternalUserTests(AuthenticationAPITestCase):
    def test_admin_can_create_internal_user(self):
        self.authenticate(self.admin)
        response = self.client.post(
            reverse('users-list'),
            {
                'email': 'teacher@test.com',
                'password': 'Teacher123',
                'username': 'teacher.user',
                'first_name': 'Teacher',
                'last_name': 'One',
                'role': User.Role.TEACHER,
                'is_approved': True,
                'is_active': True,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = User.objects.get(email='teacher@test.com')
        self.assertEqual(created.role, User.Role.TEACHER)
        self.assertTrue(created.check_password('Teacher123'))

    def test_client_cannot_create_internal_user(self):
        self.authenticate(self.client_user)
        response = self.client.post(
            reverse('users-list'),
            {
                'email': 'blocked@test.com',
                'password': 'Blocked123',
                'first_name': 'Blocked',
                'last_name': 'User',
                'role': User.Role.TEACHER,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class HU02ListInternalUsersTests(AuthenticationAPITestCase):
    def setUp(self):
        super().setUp()
        User.objects.create_user(
            username='teacher.user',
            email='teacher@test.com',
            password='Teacher123',
            role=User.Role.TEACHER,
            is_approved=True,
        )

    def test_admin_lists_internal_users_with_role_filter(self):
        self.authenticate(self.admin)
        response = self.client.get(reverse('users-list'), {'role': User.Role.TEACHER})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emails = [item['email'] for item in response.data]
        self.assertIn('teacher@test.com', emails)
        self.assertNotIn('client@test.com', emails)


class HU03UpdateInternalUserTests(AuthenticationAPITestCase):
    def setUp(self):
        super().setUp()
        self.teacher = User.objects.create_user(
            username='teacher.user',
            email='teacher@test.com',
            password='Teacher123',
            role=User.Role.TEACHER,
            is_approved=True,
        )

    def test_admin_updates_internal_user(self):
        self.authenticate(self.admin)
        response = self.client.patch(
            reverse('users-detail', kwargs={'pk': self.teacher.pk}),
            {'first_name': 'Updated'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.teacher.refresh_from_db()
        self.assertEqual(self.teacher.first_name, 'Updated')


class HU04SoftDeleteInternalUserTests(AuthenticationAPITestCase):
    def setUp(self):
        super().setUp()
        self.teacher = User.objects.create_user(
            username='teacher.user',
            email='teacher@test.com',
            password='Teacher123',
            role=User.Role.TEACHER,
            is_approved=True,
        )

    def test_admin_soft_deletes_internal_user(self):
        self.authenticate(self.admin)
        response = self.client.delete(reverse('users-detail', kwargs={'pk': self.teacher.pk}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.teacher.refresh_from_db()
        self.assertFalse(self.teacher.is_active)
        self.assertTrue(User.objects.filter(pk=self.teacher.pk).exists())


class HU05LoginTests(AuthenticationAPITestCase):
    @override_settings(DEBUG=True)
    def test_login_returns_jwt_with_dev_captcha(self):
        response = self.client.post(
            reverse('auth-login'),
            {
                'email': 'admin@test.com',
                'password': 'AdminPass123',
                'captcha_token': 'dev-bypass',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['email'], 'admin@test.com')


class HU06RegisterClientTests(AuthenticationAPITestCase):
    def test_client_registers_with_pending_approval(self):
        response = self.client.post(
            reverse('users-register'),
            {
                'email': 'newclient@test.com',
                'password': 'ClientPass123',
                'password_confirm': 'ClientPass123',
                'first_name': 'New',
                'last_name': 'Client',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = User.objects.get(email='newclient@test.com')
        self.assertEqual(created.role, User.Role.CLIENT)
        self.assertFalse(created.is_approved)


class HU07ClientProfileTests(AuthenticationAPITestCase):
    def test_client_views_and_updates_profile(self):
        self.authenticate(self.client_user)
        get_response = self.client.get(reverse('users-me'))
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data['email'], 'client@test.com')

        patch_response = self.client.patch(
            reverse('users-me'),
            {'first_name': 'UpdatedClient'},
            format='json',
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.client_user.refresh_from_db()
        self.assertEqual(self.client_user.first_name, 'UpdatedClient')
