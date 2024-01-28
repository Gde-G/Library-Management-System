import pdb

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.test.test_setup import RegularUserAPITest

from ..models import Reservation, Strike
from .factories import ReservationFactory


class AuthStrikeRetrieveAPITest(RegularUserAPITest, ReservationFactory):
    def test_strikes_previously_not_exists(self):
        url = reverse('strikes-list')

        response = self.client.get(
            url
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('detail', response.data.keys())

    def test_strikes_previously_exists(self):
        dates = self.start_end_dates()
        res = Reservation.objects.create(
            user=self.user,
            book=self.book(),
            start_date=dates[0],
            end_date=dates[1],
            initial_price=10.00,
        )
        Strike.objects.create(
            reservation=res,
            reason="Test case with out creating with celery."
        )

        url = reverse('strikes-list')
        response = self.client.get(
            url
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn('reservation', response.data[0].keys())


class AuthStrikesAmountAPITest(RegularUserAPITest, ReservationFactory):
    def test_amount_strikes_0(self):
        url = reverse('strikes-amount')
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('amount_strikes', response.data.keys())
        self.assertEqual(response.data['amount_strikes'], 0)

    def test_amount_strikes_3(self):
        for _ in range(3):
            dates = self.start_end_dates()
            res = Reservation.objects.create(
                user=self.user,
                book=self.book(),
                start_date=dates[0],
                end_date=dates[1],
                initial_price=10.00,
            )
            Strike.objects.create(
                reservation=res,
                reason="Test case with out creating with celery."
            )

        url = reverse('strikes-amount')
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('amount_strikes', response.data.keys())
        self.assertEqual(response.data['amount_strikes'], 3)

    def test_amount_strikes_6(self):
        for _ in range(6):
            dates = self.start_end_dates()
            res = Reservation.objects.create(
                user=self.user,
                book=self.book(),
                start_date=dates[0],
                end_date=dates[1],
                initial_price=10.00,
            )
            Strike.objects.create(
                reservation=res,
                reason="Test case with out creating with celery."
            )

        url = reverse('strikes-amount')
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('amount_strikes', response.data.keys())
        self.assertEqual(response.data['amount_strikes'], 6)

    def test_amount_strikes_9(self):
        for _ in range(9):
            dates = self.start_end_dates()
            res = Reservation.objects.create(
                user=self.user,
                book=self.book(),
                start_date=dates[0],
                end_date=dates[1],
                initial_price=10.00,
            )
            Strike.objects.create(
                reservation=res,
                reason="Test case with out creating with celery."
            )

        url = reverse('strikes-amount')
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('amount_strikes', response.data.keys())
        self.assertEqual(response.data['amount_strikes'], 9)


class NoAuthStrikeRetrieveAPITest(APITestCase):
    def test_strikes_previously_not_exists(self):
        url = reverse('strikes-list')

        response = self.client.get(
            url
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
