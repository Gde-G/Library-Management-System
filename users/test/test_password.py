import pdb

from django.urls import reverse

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from core.test.test_setup import AdminUserAPITest, RegularUserAPITest
from .factories import UserFactory
from ..models import User


class PasswordCheckMatchAPITest(APITestCase):
    def test_check_password_match_true(self):
        data = {
            'password': 'LolaMento40',
            'password2': 'LolaMento40'
        }

        url = reverse('check_password_match')
        response = self.client.post(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['match'])

    def test_check_password_match_false(self):
        data = {
            'password': 'LolaMento40',
            'password2': 'LolaMentoFallo40'
        }

        url = reverse('check_password_match')
        response = self.client.post(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['match'])

    def test_fail_check_password_match(self):
        data = {
            'password': 'LolaMento40',
        }

        url = reverse('check_password_match')
        response = self.client.post(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AuthPasswordChangeAPITest(RegularUserAPITest):
    def test_password_change_successfully(self):
        data = {
            'old_password': 'testpassword',
            'new_password': 'NewPassword123',
            'confirm_new_password': 'NewPassword123'
        }

        url = reverse('password-change')
        response = self.client.post(
            url,
            data
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.get_access_token(password=data['new_password'])

    def test_password_change_fail_weak_password(self):
        data = {
            'old_password': 'testpassword',
            'new_password': 'weak',
            'confirm_new_password': 'weak'
        }

        url = reverse('password-change')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', response.data)

    def test_password_change_fail_incorrect_old_password(self):
        data = {
            'old_password': 'incorrect_password',
            'new_password': 'NewPassword123',
            'confirm_new_password': 'NewPassword123'
        }

        url = reverse('password-change')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('old_password', response.data)

    def test_password_change_fail_mismatched_new_passwords(self):
        data = {
            'old_password': 'testpassword',
            'new_password': 'NewPassword123',
            'confirm_new_password': 'MismatchedPassword'
        }

        url = reverse('password-change')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('confirm_new_password', response.data)
