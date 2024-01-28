from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework.test import APIClient
from rest_framework import status
from faker import Faker
import pdb

faker = Faker()


class AdminUserAPITest(APITestCase):
    def setUp(self):
        self.user = self.create_test_user()

        self.token = self.get_access_token()

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    def create_test_user(self):
        return get_user_model().objects.create_user(
            username='testuser-admin',
            password='testpassword',
            email=faker.email(),
            first_name='perror',
            last_name='Malongo',
            is_active=True,
            is_staff=True,
            is_superuser=True
        )

    def get_access_token(self):
        response = self.client.post(
            '/token/', {'username': self.user.username, 'password': 'testpassword'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials()
        return response.data['access']

    def test_setup(self):
        pass


class RegularUserAPITest(APITestCase):
    def setUp(self):
        self.user = self.create_test_user()

        self.token = self.get_access_token()

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    def create_test_user(self):
        return get_user_model().objects.create_user(
            username='testuser-common',
            password='testpassword',
            email=faker.email(),
            first_name='Diego',
            last_name='Malongo',
            is_active=True,
            is_staff=False,
            is_superuser=False
        )

    def get_access_token(self, password='testpassword'):
        response = self.client.post(
            '/token/', {'username': self.user.username, 'password': password})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials()
        return response.data['access']

    def test_setup(self):
        pass
