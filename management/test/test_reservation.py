import pdb
import datetime
from decimal import Decimal
from freezegun import freeze_time

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.test.test_setup import AdminUserAPITest, RegularUserAPITest

from .factories import ReservationFactory
from ..utils_models import calculate_initial_price
from ..models import Reservation, Notification
from ..utils import create_penalty
from ..tasks import (
    reservation_confirm_to_available, reservation_end_and_never_pickup,
    reservation_retired_to_expire
)


class AuthCreateReservationAPITest(RegularUserAPITest, ReservationFactory):
    def test_create_reservation_needy_fields(self):

        data = self.reservation_as_data(user=self.user)

        url = reverse('reservation-list')
        response = self.client.post(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Reservation.objects.filter(
            user=self.user.username, book=data['book']).exists())

    def test_create_reservation_with_note(self):
        data = self.reservation_as_data(user=self.user, notes=self.note())

        url = reverse('reservation-list')
        response = self.client.post(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        reservation = Reservation.objects.filter(
            user=self.user.username, book=data['book'])

        self.assertTrue(reservation.exists())
        self.assertIsNotNone(reservation.first().notes)

    def test_create_reservation_fail_pass_start_date(self):
        book = self.book()
        start_date = datetime.date.today() - datetime.timedelta(days=1)
        reservation_dates = self.start_end_dates()
        data = {
            'user': self.user.username,
            'book': book.slug,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': reservation_dates[1],

        }

        url = reverse('reservation-list')
        response = self.client.post(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('start_date', response.data.keys())

    def test_create_reservation_fail_end_date_before_start_date(self):
        book = self.book()
        start_date = datetime.date.today() - datetime.timedelta(days=1)
        reservation_dates = self.start_end_dates()
        data = {
            'user': self.user.username,
            'book': book.slug,
            'start_date': reservation_dates[1],
            'end_date': reservation_dates[0],

        }

        url = reverse('reservation-list')
        response = self.client.post(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('end_date', response.data.keys())

    def test_create_reservation_fail_not_available_same_dates(self):
        book = self.book()
        reservation_dates = self.start_end_dates()

        data = {
            'user': self.user.username,
            'book': book.slug,
            'start_date': reservation_dates[0],
            'end_date': reservation_dates[1],
        }

        url = reverse('reservation-list')
        response = self.client.post(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(Reservation.objects.filter(
            user=self.user.username, book=book.slug).exists())

        response2 = self.client.post(
            url,
            data
        )

        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('book', response2.data.keys())

    def test_create_reservation_fail_not_available_start_date_in_period(self):
        book = self.book()

        data = {
            'user': self.user.username,
            'book': book.slug,
            'start_date': datetime.date.today().strftime('%Y-%m-%d'),
            'end_date': (datetime.date.today() + datetime.timedelta(days=7)).strftime('%Y-%m-%d'),
        }

        url = reverse('reservation-list')
        response = self.client.post(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(Reservation.objects.filter(
            user=self.user.username, book=book.slug).exists())

        data2 = {
            'user': self.user.username,
            'book': book.slug,
            'start_date': (datetime.date.today() + datetime.timedelta(days=3)).strftime('%Y-%m-%d'),
            'end_date': (datetime.date.today() + datetime.timedelta(days=10)).strftime('%Y-%m-%d'),
        }
        response2 = self.client.post(
            url,
            data2
        )

        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('book', response2.data.keys())

    def test_create_reservation_fail_not_available_end_date_in_period(self):
        book = self.book()

        data = {
            'user': self.user.username,
            'book': book.slug,
            'start_date': (datetime.date.today() + datetime.timedelta(days=3)).strftime('%Y-%m-%d'),
            'end_date': (datetime.date.today() + datetime.timedelta(days=10)).strftime('%Y-%m-%d'),
        }

        url = reverse('reservation-list')
        response = self.client.post(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(Reservation.objects.filter(
            user=self.user.username, book=book.slug).exists())

        data2 = {
            'user': self.user.username,
            'book': book.slug,
            'start_date': datetime.date.today().strftime('%Y-%m-%d'),
            'end_date': (datetime.date.today() + datetime.timedelta(days=7)).strftime('%Y-%m-%d'),
        }
        response2 = self.client.post(
            url,
            data2
        )

        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('book', response2.data.keys())

    def test_create_reservation_fail_not_available_both_dates_in_period(self):
        book = self.book()

        data = {
            'user': self.user.username,
            'book': book.slug,
            'start_date': datetime.date.today().strftime('%Y-%m-%d'),
            'end_date': (datetime.date.today() + datetime.timedelta(days=15)).strftime('%Y-%m-%d'),
        }

        url = reverse('reservation-list')
        response = self.client.post(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(Reservation.objects.filter(
            user=self.user.username, book=book.slug).exists())

        data2 = {
            'user': self.user.username,
            'book': book.slug,
            'start_date': (datetime.date.today() + datetime.timedelta(days=3)).strftime('%Y-%m-%d'),
            'end_date': (datetime.date.today() + datetime.timedelta(days=8)).strftime('%Y-%m-%d'),
        }
        response2 = self.client.post(
            url,
            data2
        )

        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('book', response2.data.keys())

    def test_create_reservation_fail_user_is_penalized(self):
        book = self.book()
        reservation_dates = self.start_end_dates()

        penalization = create_penalty(user=self.user)

        data = {
            'user': self.user.username,
            'book': book.slug,
            'start_date': reservation_dates[0],
            'end_date': reservation_dates[1],
            'notes': self.note()

        }

        url = reverse('reservation-list')
        response = self.client.post(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(
            'You are not allowed to reserve a book at this time, there is a penalty in effect.',
            response.data['detail']
        )


class AuthListReservationAPITest(RegularUserAPITest, ReservationFactory):

    def test_list_reservations(self):
        for _ in range(3):
            dates = self.start_end_dates()
            Reservation.objects.create(
                user=self.user,
                book=self.book(),
                start_date=dates[0],
                end_date=dates[1],
                initial_price=10.00,
            )

        url = reverse('reservation-list')
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 3)

    def test_list_reservations_paginator(self):
        for _ in range(6):
            dates = self.start_end_dates()
            Reservation.objects.create(
                user=self.user,
                book=self.book(),
                start_date=dates[0],
                end_date=dates[1],
                initial_price=10.00,
            )

        url = reverse('reservation-list')
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 6)
        self.assertEqual(len(response.data['results']), 3)
        self.assertIsNotNone(response.data['next'])

    def test_list_reservations_not_found(self):
        url = reverse('reservation-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AuthRetrieveReservationAPITest(RegularUserAPITest, ReservationFactory):
    def test_retrieve_reservations(self):

        dates = self.start_end_dates()
        reservation = Reservation.objects.create(
            user=self.user,
            book=self.book(),
            start_date=dates[0],
            end_date=dates[1],
            initial_price=10.00,
        )

        url = reverse('reservation-detail', kwargs={'pk': reservation.id})
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['book']
                         ['title'], reservation.book.title)

    def test_retrieve_reservations_not_found(self):
        url = reverse('reservation-detail', kwargs={'pk': 2342})
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_reservations_invalid_pk(self):
        url = reverse('reservation-detail', kwargs={'pk': 'slalom'})
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Celery Worker
    def test_retrieve_reservations_changes_status_available(self):

        dates = self.start_end_dates()
        res = Reservation.objects.create(
            user=self.user,
            book=self.book(),
            start_date=dates[0],
            end_date=dates[1],
            initial_price=10.00,
        )

        url = reverse('reservation-detail', kwargs={'pk': res.id})
        time_of_test = datetime.datetime.strptime(
            dates[0], '%Y-%m-%d') + datetime.timedelta(hours=10)

        with freeze_time(time_of_test.strftime("%Y-%m-%d %H:%M:%S")):
            self.token = self.get_access_token()

            self.client.credentials(
                HTTP_AUTHORIZATION='Bearer ' + self.token)

            response = self.client.get(
                url
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            self.assertEqual(
                response.data['status'], 'confirmed')

    def test_retrieve_reservations_changes_status_completed_never_pickup(self):

        dates = self.start_end_dates()
        res = Reservation.objects.create(
            user=self.user,
            book=self.book(),
            start_date=datetime.date.today(),
            end_date=dates[1],
            initial_price=10.00,
            status='available'
        )

        url = reverse('reservation-detail', kwargs={'pk': res.id})
        time_of_test = datetime.datetime.strptime(
            dates[1], '%Y-%m-%d') + datetime.timedelta(days=3)

        with freeze_time(time_of_test.strftime("%Y-%m-%d %H:%M:%S")):
            self.token = self.get_access_token()

            self.client.credentials(
                HTTP_AUTHORIZATION='Bearer ' + self.token)

            response = self.client.get(
                url
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            self.assertEqual(
                response.data['status'], 'available')

    def test_retrieve_reservations_changes_status_expired(self):

        dates = self.start_end_dates()
        res = Reservation.objects.create(
            user=self.user,
            book=self.book(),
            start_date=datetime.date.today(),
            end_date=dates[1],
            initial_price=10.00,
            status='retired'
        )

        url = reverse('reservation-detail', kwargs={'pk': res.id})
        time_of_test = datetime.datetime.strptime(
            dates[1], '%Y-%m-%d') + datetime.timedelta(days=3)

        with freeze_time(time_of_test.strftime("%Y-%m-%d %H:%M:%S")):
            self.token = self.get_access_token()

            self.client.credentials(
                HTTP_AUTHORIZATION='Bearer ' + self.token)

            response = self.client.get(
                url
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            self.assertEqual(
                response.data['status'], 'retired')


class AdminUpdateReservationAPITest(AdminUserAPITest, ReservationFactory):
    def test_update_put_method_not_allowed(self):
        dates = self.start_end_dates()
        reservation = Reservation.objects.create(
            user=self.user,
            book=self.book(),
            start_date=dates[0],
            end_date=dates[1],
            initial_price=10.00,
        )

        url = reverse('reservation-detail', kwargs={'pk': reservation.id})
        response = self.client.put(
            url
        )
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_patch_returned_on_time(self):

        dates = self.start_end_dates()
        reservation = Reservation.objects.create(
            user=self.user,
            book=self.book(),
            start_date=dates[0],
            end_date=dates[1],
            initial_price=10.00,
        )
        returned_date = datetime.datetime.strptime(
            dates[1], '%Y-%m-%d') - datetime.timedelta(hours=10)
        data = {
            'returned_date': returned_date.strftime('%Y-%m-%d')
        }
        url = reverse('reservation-detail', kwargs={'pk': reservation.id})
        response = self.client.patch(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('result', response.data.keys())
        self.assertEqual(
            response.data['result']['returned_date'], returned_date.strftime('%Y-%m-%d'))
        self.assertEqual(
            response.data['result']['penalty_price'], '0.00')
        self.assertEqual(
            response.data['result']['initial_price'],
            response.data['result']['final_price']
        )

    def test_update_patch_returned_expire_time(self):

        dates = self.start_end_dates()
        reservation = Reservation.objects.create(
            user=self.user,
            book=self.book(),
            start_date=dates[0],
            end_date=dates[1],
            initial_price=10.00,
        )
        returned_date = datetime.datetime.strptime(
            dates[1], '%Y-%m-%d') + datetime.timedelta(days=2)
        data = {
            'returned_date': returned_date.strftime('%Y-%m-%d')
        }
        url = reverse('reservation-detail', kwargs={'pk': reservation.id})
        response = self.client.patch(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('result', response.data.keys())
        self.assertEqual(
            response.data['result']['returned_date'], returned_date.strftime('%Y-%m-%d'))
        self.assertEqual(
            response.data['result']['penalty_price'], '8.00')

        self.assertNotEqual(
            response.data['result']['initial_price'],
            response.data['result']['final_price']
        )
        self.assertNotEqual(
            response.data['result']['initial_price'] +
            response.data['result']['penalty_price'],
            response.data['result']['final_price']
        )

    def test_update_patch_retired_expire_time(self):
        dates = self.start_end_dates()
        reservation = Reservation.objects.create(
            user=self.user,
            book=self.book(),
            start_date=dates[0],
            end_date=dates[1],
            initial_price=10.00,
        )

        returned_date = datetime.datetime.strptime(
            dates[1], '%Y-%m-%d') + datetime.timedelta(days=2)

        with freeze_time(returned_date.strftime("%Y-%m-%d %H:%M:%S")):
            self.token = self.get_access_token()

            self.client.credentials(
                HTTP_AUTHORIZATION='Bearer ' + self.token)

            data = {
                'retired': True
            }

            url = reverse('reservation-detail', kwargs={'pk': reservation.id})
            response = self.client.patch(
                url,
                data
            )

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_patch_retired_on_time(self):
        dates = self.start_end_dates()
        reservation = Reservation.objects.create(
            user=self.user,
            book=self.book(),
            start_date=dates[0],
            end_date=dates[1],
            initial_price=10.00,
        )

        data = {
            'retired': True
        }
        url = reverse('reservation-detail', kwargs={'pk': reservation.id})
        response = self.client.patch(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('result', response.data.keys())
        self.assertEqual(response.data['result']['status'], 'retired')

    def test_update_patch_fail_unexpected_fields(self):
        dates = self.start_end_dates()
        reservation = Reservation.objects.create(
            user=self.user,
            book=self.book(),
            start_date=dates[0],
            end_date=dates[1],
            initial_price=10.00,
        )
        returned_date = datetime.datetime.strptime(
            dates[1], '%Y-%m-%d') + datetime.timedelta(days=2)
        data = {
            'initial_price': 4.00,
            'returned_date': returned_date.strftime('%Y-%m-%d')
        }
        url = reverse('reservation-detail', kwargs={'pk': reservation.id})
        response = self.client.patch(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('result', response.data.keys())
        self.assertEqual(
            response.data['result']['returned_date'], returned_date.strftime('%Y-%m-%d'))
        self.assertNotEqual(
            response.data['result']['initial_price'], data['initial_price'])
        self.assertEqual(
            response.data['result']['penalty_price'], '8.00')

        self.assertNotEqual(
            response.data['result']['initial_price'],
            response.data['result']['final_price']
        )
        self.assertNotEqual(
            response.data['result']['initial_price'] +
            response.data['result']['penalty_price'],
            response.data['result']['final_price']
        )

    def test_update_patch_fail_reservation_not_found(self):
        url = reverse('reservation-detail', kwargs={'pk': 2342})
        response = self.client.patch(
            url,
            {
                'returned_data': '2024-03-03'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_patch_fail_invalid_pk(self):
        url = reverse('reservation-detail', kwargs={'pk': 'sologomongo'})
        response = self.client.patch(
            url,
            {
                'returned_data': '2024-03-03'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AuthDestroyReservationAPITest(RegularUserAPITest, ReservationFactory):
    def test_destroy_reservation_on_time(self):
        dates = self.start_end_dates()
        reservation = Reservation.objects.create(
            user=self.user,
            book=self.book(),
            start_date=dates[0],
            end_date=dates[1],
            initial_price=10.00,
        )
        cancel_date = datetime.datetime.strptime(
            dates[0], '%Y-%m-%d') - datetime.timedelta(hours=10)

        url = reverse('reservation-detail', kwargs={'pk': reservation.id})

        with freeze_time(cancel_date.strftime("%Y-%m-%d %H:%M:%S")):
            self.token = self.get_access_token()
            self.client.credentials(
                HTTP_AUTHORIZATION='Bearer ' + self.token)

            response = self.client.delete(url)

            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            reservation.refresh_from_db()
            self.assertEqual(reservation.status, 'canceled_user')

    def test_destroy_reservation_fail_already_start_reservation(self):
        dates = self.start_end_dates()
        reservation = Reservation.objects.create(
            user=self.user,
            book=self.book(),
            start_date=dates[0],
            end_date=dates[1],
            initial_price=10.00,
        )
        cancel_date = datetime.datetime.strptime(
            dates[0], '%Y-%m-%d') + datetime.timedelta(hours=10)

        url = reverse('reservation-detail', kwargs={'pk': reservation.id})

        with freeze_time(cancel_date.strftime("%Y-%m-%d %H:%M:%S")):
            self.token = self.get_access_token()
            self.client.credentials(
                HTTP_AUTHORIZATION='Bearer ' + self.token)

            response = self.client.delete(url)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_reservation_fail_not_found(self):
        url = reverse('reservation-detail', kwargs={'pk': 1222})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_destroy_reservation_invalid_pk(self):
        url = reverse('reservation-detail', kwargs={'pk': 'somlodmy'})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AuthCheckAvailabilityReservationAPITest(RegularUserAPITest, ReservationFactory):
    def test_check_availability_true(self):
        book = self.book()
        url = reverse('reservation-check-availability')
        response = self.client.get(
            url,
            {
                'book': book.slug,
                'start_date': '2024-02-03',
                'end_date': '2024-02-10'
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['is_available'], True)

    def test_check_availability_false_some_period(self):
        dates = self.start_end_dates()
        reservation = Reservation.objects.create(
            user=self.user,
            book=self.book(),
            start_date=dates[0],
            end_date=dates[1],
            initial_price=10.00,
        )
        url = reverse('reservation-check-availability')
        response = self.client.get(
            url,
            {
                'book': reservation.book.slug,
                'start_date': dates[0],
                'end_date': dates[1]
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['is_available'], False)

    def test_check_availability_false_previous_start_date_intersection(self):
        dates = self.start_end_dates()
        reservation = Reservation.objects.create(
            user=self.user,
            book=self.book(),
            start_date=dates[0],
            end_date=dates[1],
            initial_price=10.00,
        )
        url = reverse('reservation-check-availability')
        start_date = datetime.datetime.strptime(
            dates[0], '%Y-%m-%d') - datetime.timedelta(days=1)
        response = self.client.get(
            url,
            {
                'book': reservation.book.slug,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': dates[1]
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['is_available'], False)

    def test_check_availability_false_later_start_date_intersection(self):
        dates = self.start_end_dates()
        reservation = Reservation.objects.create(
            user=self.user,
            book=self.book(),
            start_date=dates[0],
            end_date=dates[1],
            initial_price=10.00,
        )
        url = reverse('reservation-check-availability')
        start_date = datetime.datetime.strptime(
            dates[0], '%Y-%m-%d') + datetime.timedelta(days=1)
        response = self.client.get(
            url,
            {
                'book': reservation.book.slug,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': dates[1]
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['is_available'], False)

    def test_check_availability_fail_book_not_send(self):
        url = reverse('reservation-check-availability')
        dates = self.start_end_dates()
        response = self.client.get(
            url,
            {
                'start_date': dates[0],
                'end_date': dates[1]
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('book', response.data.keys())

    def test_check_availability_fail_book_not_found(self):
        url = reverse('reservation-check-availability')
        dates = self.start_end_dates()
        response = self.client.get(
            url,
            {
                'book': 'reservation-book-slug',
                'start_date': dates[0],
                'end_date': dates[1]
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('book', response.data.keys())

    def test_check_availability_fail_start_date_not_send(self):
        url = reverse('reservation-check-availability')
        dates = self.start_end_dates()
        response = self.client.get(
            url,
            {
                'book': self.book().slug,
                'start_date': 'kejejeje',
                'end_date': dates[1]
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('start_date', response.data.keys())

    def test_check_availability_fail_start_date_invalid(self):
        url = reverse('reservation-check-availability')
        dates = self.start_end_dates()
        response = self.client.get(
            url,
            {
                'book': self.book().slug,
                'start_date': 'kejejeje',
                'end_date': dates[1]
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('start_date', response.data.keys())

    def test_check_availability_fail_end_date_not_send(self):
        url = reverse('reservation-check-availability')
        dates = self.start_end_dates()
        response = self.client.get(
            url,
            {
                'book': self.book().slug,
                'start_date': dates[1]
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('end_date', response.data.keys())

    def test_check_availability_fail_end_date_invalid(self):
        url = reverse('reservation-check-availability')
        dates = self.start_end_dates()
        response = self.client.get(
            url,
            {
                'book': self.book().slug,
                'start_date': dates[1],
                'end_date': 'kejejeje',

            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('end_date', response.data.keys())


class AuthListUnavailablePeriodsToReservationAPITest(RegularUserAPITest, ReservationFactory):
    def test_list_unavailable_periods(self):
        book = self.book()
        for _ in range(6):
            dates = self.start_end_dates()
            try:
                Reservation.objects.create(
                    user=self.user,
                    book=book,
                    start_date=dates[0],
                    end_date=dates[1],
                    initial_price=10.00,
                )
            except:
                pass

        url = reverse('reservation-unavailable-periods')
        response = self.client.get(
            url,
            {'book': book.slug}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_unavailable_periods_not_founds(self):
        url = reverse('reservation-unavailable-periods')
        response = self.client.get(
            url,
            {'book': 'book-slug'}
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_unavailable_periods_fail_book_not_send(self):
        url = reverse('reservation-unavailable-periods')
        response = self.client.get(
            url,

        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('book', response.data.keys())
