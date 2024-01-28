import pdb

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.test.test_setup import RegularUserAPITest

from ..models import Reservation, Strike
from ..utils import add_strike_to_strike_group
from .factories import ReservationFactory


class AuthPenaltyListAPITest(RegularUserAPITest, ReservationFactory):
    def test_list_penalty(self):
        for _ in range(3):
            dates = self.start_end_dates()
            res = Reservation.objects.create(
                user=self.user,
                book=self.book(),
                start_date=dates[0],
                end_date=dates[1],
                initial_price=10.00,
            )
            strike = Strike.objects.create(
                reservation=res,
                reason="Test case with out creating with celery."
            )

            strike_group = add_strike_to_strike_group(self.user, strike)

        url = reverse('penalty-list')
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn('id', response.data[0].keys())
        self.assertIn('start_date', response.data[0].keys())
        self.assertIn('end_date', response.data[0].keys())
        self.assertIn('user', response.data[0].keys())

    def test_list_penalties_2(self):
        for _ in range(6):
            dates = self.start_end_dates()
            res = Reservation.objects.create(
                user=self.user,
                book=self.book(),
                start_date=dates[0],
                end_date=dates[1],
                initial_price=10.00,
            )
            strike = Strike.objects.create(
                reservation=res,
                reason="Test case with out creating with celery."
            )

            strike_group = add_strike_to_strike_group(self.user, strike)

        url = reverse('penalty-list')
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertIn('id', response.data[0].keys())
        self.assertIn('start_date', response.data[0].keys())
        self.assertIn('end_date', response.data[0].keys())
        self.assertIn('user', response.data[0].keys())

    def test_list_penalties_3(self):
        for _ in range(9):
            dates = self.start_end_dates()
            res = Reservation.objects.create(
                user=self.user,
                book=self.book(),
                start_date=dates[0],
                end_date=dates[1],
                initial_price=10.00,
            )
            strike = Strike.objects.create(
                reservation=res,
                reason="Test case with out creating with celery."
            )

            strike_group = add_strike_to_strike_group(self.user, strike)

        url = reverse('penalty-list')
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertIn('id', response.data[0].keys())
        self.assertIn('start_date', response.data[0].keys())
        self.assertIn('end_date', response.data[0].keys())
        self.assertIn('user', response.data[0].keys())

    def test_retrieve_penalty_not_found(self):
        url = reverse('penalty-list')
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AuthPenaltyRetrieveAPITest(RegularUserAPITest, ReservationFactory):
    def test_retrieve_penalty(self):
        for _ in range(3):
            dates = self.start_end_dates()
            res = Reservation.objects.create(
                user=self.user,
                book=self.book(),
                start_date=dates[0],
                end_date=dates[1],
                initial_price=10.00,
            )
            strike = Strike.objects.create(
                reservation=res,
                reason="Test case with out creating with celery."
            )

            strike_group = add_strike_to_strike_group(self.user, strike)

        url = reverse('penalty-detail', kwargs={'pk': strike_group.penalty.id})
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('penalty', response.data.keys())
        self.assertIn('strikes', response.data.keys())

    def test_retrieve_penalty_not_found(self):
        url = reverse('penalty-detail', kwargs={'pk': 232})
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AuthPenaltyAmountAPITest(RegularUserAPITest, ReservationFactory):
    def test_amount_penalties_0(self):
        url = reverse('penalty-amount')
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('amount_penalties', response.data.keys())
        self.assertEqual(response.data['amount_penalties'], 0)

    def test_amount_penalties_1(self):
        for _ in range(3):
            dates = self.start_end_dates()
            res = Reservation.objects.create(
                user=self.user,
                book=self.book(),
                start_date=dates[0],
                end_date=dates[1],
                initial_price=10.00,
            )
            strike = Strike.objects.create(
                reservation=res,
                reason="Test case with out creating with celery."
            )

            strike_group = add_strike_to_strike_group(self.user, strike)
        url = reverse('penalty-amount')
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('amount_penalties', response.data.keys())
        self.assertEqual(response.data['amount_penalties'], 1)

    def test_amount_penalties_2(self):
        for _ in range(6):
            dates = self.start_end_dates()
            res = Reservation.objects.create(
                user=self.user,
                book=self.book(),
                start_date=dates[0],
                end_date=dates[1],
                initial_price=10.00,
            )
            strike = Strike.objects.create(
                reservation=res,
                reason="Test case with out creating with celery."
            )

            strike_group = add_strike_to_strike_group(self.user, strike)
        url = reverse('penalty-amount')
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('amount_penalties', response.data.keys())
        self.assertEqual(response.data['amount_penalties'], 2)

    def test_amount_penalties_3(self):
        for _ in range(9):
            dates = self.start_end_dates()
            res = Reservation.objects.create(
                user=self.user,
                book=self.book(),
                start_date=dates[0],
                end_date=dates[1],
                initial_price=10.00,
            )
            strike = Strike.objects.create(
                reservation=res,
                reason="Test case with out creating with celery."
            )

            strike_group = add_strike_to_strike_group(self.user, strike)
        url = reverse('penalty-amount')
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('amount_penalties', response.data.keys())
        self.assertEqual(response.data['amount_penalties'], 3)


class NoAuthPenaltyAPITest(APITestCase):
    def test__penalty_fail_not_auth(self):
        url = reverse('penalty-list')
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class NoAuthPenaltyAPITest(APITestCase):
    def test__penalty_fail_not_auth(self):
        url = reverse('penalty-detail', kwargs={'pk': 1})
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
