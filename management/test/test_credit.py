import pdb

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.test.test_setup import AdminUserAPITest, RegularUserAPITest

from ..models import Credit


class AuthCreditListAPITest(RegularUserAPITest):
    def test_credits_previously_not_exists(self):
        url = reverse('credits-list')

        response = self.client.get(
            url
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data.keys())
        self.assertEqual(response.data['user'], self.user.username)
        self.assertIn('amount', response.data.keys())
        self.assertEqual(response.data['amount'], 0)

    def test_credits_previously_exists(self):
        Credit.objects.create(
            user=self.user,
            amount=4
        )
        url = reverse('credits-list')
        response = self.client.get(
            url
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.user.username)
        self.assertEqual(response.data['amount'], 4)


class AdminCreditSubtractAPITest(AdminUserAPITest):
    def test_credit_subtract(self):
        credits = Credit.objects.create(
            user=self.user,
            amount=4
        )
        url = reverse('credits-subtract')
        response = self.client.patch(
            url,
            {
                'subtract': 2
            }
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('credits', response.data.keys())
        self.assertEqual(response.data['credits']['amount'], 2)
        credits.refresh_from_db()
        self.assertEqual(credits.amount, 2)

    def test_credit_subtract_fail_invalid_subtract_type(self):
        credits = Credit.objects.create(
            user=self.user,
            amount=4
        )
        url = reverse('credits-subtract')
        response = self.client.patch(
            url,
            {
                'subtract': 'jaja'
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_credit_subtract_fail_invalid_subtract_value_negative(self):
        credits = Credit.objects.create(
            user=self.user,
            amount=4
        )
        url = reverse('credits-subtract')
        response = self.client.patch(
            url,
            {
                'subtract': -5
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_credit_subtract_fail_invalid_subtract_value_more_than_amount(self):
        credits = Credit.objects.create(
            user=self.user,
            amount=4
        )
        url = reverse('credits-subtract')
        response = self.client.patch(
            url,
            {
                'subtract': 5
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class NoAuthCreditRetrieveAPITest(APITestCase):
    def test_credits_list_fail_not_auth(self):
        url = reverse('credits-list')

        response = self.client.get(
            url
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class NoAuthCreditRetrieveAPITest(APITestCase):
    def test_credits_fail_subtract_not_auth(self):
        url = reverse('credits-subtract')

        response = self.client.get(
            url
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
