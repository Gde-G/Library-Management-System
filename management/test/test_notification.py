import pdb
import pytest
import datetime
import time
from decimal import Decimal
from freezegun import freeze_time

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.test.test_setup import RegularUserAPITest

from .factories import ReservationFactory
from ..models import Reservation, Notification
from ..utils import create_notification, create_strike


class AuthNotificationListAPITest(RegularUserAPITest, ReservationFactory):

    def test_notification_list(self):
        dates = self.start_end_dates()
        res = Reservation.objects.create(
            user=self.user,
            book=self.book(),
            start_date=dates[0],
            end_date=dates[1],
            initial_price=10.00,
        )

        noti = create_notification(
            user=self.user,
            title='Notification test',
            message='Some Notification referrer to a reservation',
            obj=res
        )

        url = reverse('notification-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, response.data['count'])
        self.assertIn('type', response.data['results'][0].keys())
        self.assertIn(response.data['results'][0]
                      ['type'], response.data['results'][0].keys())

    def test_notification_list_more_than_one_obj(self):
        res = self.reservation_success(user=self.user)
        res2 = self.reservation_success(user=self.user)

        strike = create_strike(
            res=res2,
            reason="Some reason to make the test."
        )

        create_notification(
            user=self.user,
            title='Notification test',
            message='Some Notification referrer to a reservation',
            obj=res
        )
        create_notification(
            user=self.user,
            title='Some title 2',
            message="Some message to notification2",
            obj=strike
        )

        url = reverse('notification-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(2, response.data['count'])

        for i in range(len(response.data['results'])):
            self.assertIn('type', response.data['results'][i].keys())
            self.assertIn(response.data['results'][i]
                          ['type'], response.data['results'][i].keys())

    def test_notification_list_not_read(self):
        for i in range(6):
            res = self.reservation_success(user=self.user)

            noti = create_notification(
                user=self.user,
                title='Notification test',
                message='Some Notification referrer to a reservation',
                obj=res
            )
            if i % 2 == 0:
                noti.is_read = True
                noti.save()

        url = reverse('notification-list')
        response = self.client.get(
            url,
            {
                'not_read': 'true'
            }

        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(3, response.data['count'])

        for i in range(len(response.data['results'])):

            self.assertIn('type', response.data['results'][i].keys())
            self.assertIn(response.data['results'][i]
                          ['type'], response.data['results'][i].keys())
            self.assertEqual(response.data['results'][i]['is_read'], False)

    def test_notification_list_check_order(self):
        for i in range(6):
            res = self.reservation_success(user=self.user)

            noti = create_notification(
                user=self.user,
                title='Notification test',
                message='Some Notification referrer to a reservation',
                obj=res
            )
            if i % 2 == 0:
                noti.is_read = True
                noti.save()

        url = reverse('notification-list')
        response = self.client.get(
            url,
            {
                'page_size': 6,
            }

        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(6, response.data['count'])

        for i in range(response.data['count']):
            if i < 3:
                self.assertEqual(response.data['results'][i]['is_read'], False)
            else:
                self.assertEqual(response.data['results'][i]['is_read'], True)

    def test_notification_list_pagination(self):
        for i in range(6):
            res = self.reservation_success(user=self.user)

            noti = create_notification(
                user=self.user,
                title=f'Notification test {i}.',
                message='Some Notification referrer to a reservation',
                obj=res
            )

        url = reverse('notification-list')
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(6, response.data['count'])

        self.assertEqual(3, len(response.data['results']))
        self.assertIsNotNone(response.data['next'])

        response2 = self.client.get(
            response.data['next']
        )

        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(6, response2.data['count'])

        self.assertEqual(3, len(response2.data['results']))

    def test_notification_list_not_exists(self):
        url = reverse('notification-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AuthNotificationRetrieveAPITest(RegularUserAPITest, ReservationFactory):
    def test_notification_retrieve(self):
        dates = self.start_end_dates()
        res = Reservation.objects.create(
            user=self.user,
            book=self.book(),
            start_date=dates[0],
            end_date=dates[1],
            initial_price=10.00,
        )

        noti = create_notification(
            user=self.user,
            title='Notification test',
            message='Some Notification referrer to a reservation',
            obj=res
        )

        url = reverse('notification-detail', kwargs={'pk': noti.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('type', response.data.keys())

    def test_notification_retrieve_not_found(self):

        url = reverse('notification-detail', kwargs={'pk': 23})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_notification_retrieve_invalid_pk(self):

        url = reverse('notification-detail', kwargs={'pk': 'lolololol'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class NoAuthNotificationAPITest(APITestCase):
    def test_notification_list_fail_not_auth(self):
        url = reverse('notification-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_notification_retrieve_fail_not_auth(self):
        url = reverse('notification-detail', kwargs={'pk': 2})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
