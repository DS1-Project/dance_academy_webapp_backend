from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import User
from apps.choreography.models import (
    Choreography,
    ChoreographyStat,
    DanceStyle,
)
from apps.sales.models import Enrollment, Sale, SaleDetail


class SalesAPITestCase(APITestCase):
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
        self.other_client = User.objects.create_user(
            username='other.client',
            email='other@test.com',
            password='OtherPass123',
            first_name='Other',
            last_name='Client',
            role=User.Role.CLIENT,
            is_approved=True,
        )
        self.teacher = User.objects.create_user(
            username='teacher.user',
            email='teacher@test.com',
            password='TeacherPass123',
            role=User.Role.TEACHER,
            is_approved=True,
        )
        self.style = DanceStyle.objects.create(
            name='Salsa',
            description='Salsa style',
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
        self.stats = ChoreographyStat.objects.create(
            choreography=self.choreography,
            actual_price=Decimal('29.99'),
        )
        self.second_choreography = Choreography.objects.create(
            title='Salsa Intermedia',
            description='Nivel intermedio',
            difficulty_level=Choreography.Difficulty.INTERMEDIATE,
            thumbnail_url='https://example.com/thumb2.jpg',
            is_approved=True,
            main_teacher=self.teacher,
            dance_style=self.style,
        )
        ChoreographyStat.objects.create(
            choreography=self.second_choreography,
            actual_price=Decimal('39.99'),
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def create_pending_sale(self, user=None, choreographies=None):
        user = user or self.client_user
        choreographies = choreographies or [self.choreography]
        total = sum(
            Decimal(str(c.stats.actual_price)) for c in choreographies
        )
        sale = Sale.objects.create(
            client=user,
            total_amount=total,
            payment_status=Sale.PaymentStatus.PENDING,
            billing_address='Calle 1 #2-3, Cali',
        )
        for choreography in choreographies:
            SaleDetail.objects.create(
                sale=sale,
                choreography=choreography,
                unit_price=choreography.stats.actual_price,
            )
        return sale


class SaleModelTests(SalesAPITestCase):
    def test_sale_models_persist_expected_fields(self):
        sale = self.create_pending_sale()
        self.assertEqual(sale.payment_status, Sale.PaymentStatus.PENDING)
        self.assertEqual(sale.details.count(), 1)
        self.assertEqual(sale.total_amount, Decimal('29.99'))


class CreateSaleTests(SalesAPITestCase):
    def test_client_can_create_pending_sale(self):
        self.authenticate(self.client_user)
        response = self.client.post(
            reverse('sales-list'),
            {
                'choreography_ids': [str(self.choreography.id)],
                'billing_address': 'Calle 10 #20-30, Cali',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['payment_status'], 'pending')
        self.assertEqual(Decimal(response.data['total_amount']), Decimal('29.99'))
        self.assertEqual(len(response.data['details']), 1)
        sale = Sale.objects.get(id=response.data['id'])
        self.assertEqual(sale.client_id, self.client_user.id)

    def test_unapproved_choreography_is_rejected(self):
        self.choreography.is_approved = False
        self.choreography.save(update_fields=['is_approved'])
        self.authenticate(self.client_user)
        response = self.client.post(
            reverse('sales-list'),
            {
                'choreography_ids': [str(self.choreography.id)],
                'billing_address': 'Calle 10 #20-30, Cali',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_cannot_create_sale(self):
        self.authenticate(self.admin)
        response = self.client.post(
            reverse('sales-list'),
            {
                'choreography_ids': [str(self.choreography.id)],
                'billing_address': 'Calle 10 #20-30, Cali',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_buy_already_enrolled_choreography(self):
        Enrollment.objects.create(
            client=self.client_user,
            choreography=self.choreography,
        )
        self.authenticate(self.client_user)
        response = self.client.post(
            reverse('sales-list'),
            {
                'choreography_ids': [str(self.choreography.id)],
                'billing_address': 'Calle 10 #20-30, Cali',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ListSaleTests(SalesAPITestCase):
    def setUp(self):
        super().setUp()
        self.own_sale = self.create_pending_sale(self.client_user)
        self.other_sale = self.create_pending_sale(self.other_client)

    def test_client_lists_only_own_sales(self):
        self.authenticate(self.client_user)
        response = self.client.get(reverse('sales-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in response.data]
        self.assertIn(str(self.own_sale.id), ids)
        self.assertNotIn(str(self.other_sale.id), ids)

    def test_admin_lists_all_sales(self):
        self.authenticate(self.admin)
        response = self.client.get(reverse('sales-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in response.data]
        self.assertIn(str(self.own_sale.id), ids)
        self.assertIn(str(self.other_sale.id), ids)


class CheckoutTests(SalesAPITestCase):
    def test_successful_checkout_creates_enrollment_and_updates_stats(self):
        sale = self.create_pending_sale()
        self.authenticate(self.client_user)
        response = self.client.post(
            reverse('sales-checkout', kwargs={'pk': sale.pk}),
            {'success': True},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['payment_status'], 'completed')
        sale.refresh_from_db()
        self.assertEqual(sale.payment_status, Sale.PaymentStatus.COMPLETED)
        self.assertTrue(
            Enrollment.objects.filter(
                client=self.client_user,
                choreography=self.choreography,
            ).exists()
        )
        self.stats.refresh_from_db()
        self.assertEqual(self.stats.total_sales_count, 1)

    def test_failed_checkout_marks_sale_failed_without_enrollment(self):
        sale = self.create_pending_sale()
        self.authenticate(self.client_user)
        response = self.client.post(
            reverse('sales-checkout', kwargs={'pk': sale.pk}),
            {'success': False},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['payment_status'], 'failed')
        self.assertFalse(
            Enrollment.objects.filter(
                client=self.client_user,
                choreography=self.choreography,
            ).exists()
        )

    def test_other_client_cannot_checkout_foreign_sale(self):
        sale = self.create_pending_sale(self.client_user)
        self.authenticate(self.other_client)
        response = self.client.post(
            reverse('sales-checkout', kwargs={'pk': sale.pk}),
            {'success': True},
            format='json',
        )
        self.assertIn(
            response.status_code,
            {status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND},
        )

    def test_cannot_checkout_non_pending_sale(self):
        sale = self.create_pending_sale()
        sale.payment_status = Sale.PaymentStatus.COMPLETED
        sale.save(update_fields=['payment_status'])
        self.authenticate(self.client_user)
        response = self.client.post(
            reverse('sales-checkout', kwargs={'pk': sale.pk}),
            {'success': True},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class MyEnrollmentsTests(SalesAPITestCase):
    def test_client_lists_own_enrollments(self):
        Enrollment.objects.create(
            client=self.client_user,
            choreography=self.choreography,
        )
        self.authenticate(self.client_user)
        response = self.client.get(reverse('sales-my-enrollments'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]['choreography'],
            self.choreography.id,
        )
