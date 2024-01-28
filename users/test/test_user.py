import pdb

from django.urls import reverse

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from core.test.test_setup import AdminUserAPITest, RegularUserAPITest
from .factories import UserFactory
from ..models import User


class NoAuthUserTestCase(APITestCase, UserFactory):
    def test_create_user_all_fields(self):
        url = reverse('users-list')
        profile_img_data = self.profile_img().file.getvalue()

        profile_img_file = SimpleUploadedFile(
            'profile_img.jpg', profile_img_data, content_type='image/jpeg'),
        response = self.client.post(
            path=url,
            data={
                'password': 'Belgrano1905',
                'password2': 'Belgrano1905',
                'first_name': self.first_name(),
                'last_name': self.last_name(),
                'username': self.username(),
                'email': self.email(),
                'birth_date': self.birth_date(),
                'profile_img': profile_img_file,
            },
        )

        created_user = User.objects.first()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual('', created_user.profile_img)

    def test_create_user_needed_fields(self):
        url = reverse('users-list')

        response = self.client.post(
            path=url,
            data={
                'password': 'Belgrano1905',
                'password2': 'Belgrano1905',
                'first_name': self.first_name(),
                'last_name': self.last_name(),
                'username': self.username(),
                'email': self.email(),
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_fail_create_user_wrong_confirm_password(self):
        url = reverse('users-list')

        response = self.client.post(
            path=url,
            data={
                'password': 'Belgrano1905',
                'password2': 'Belgrano190',
                'first_name': self.first_name(),
                'last_name': self.last_name(),
                'username': self.username(),
                'email': self.email(),
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fail_create_user_needed_fields_not_send(self):
        url = reverse('users-list')

        response = self.client.post(
            path=url,
            data={
                'password': 'Belgrano1905',
                'password2': 'Belgrano1905',
                'first_name': self.first_name(),
                'username': self.username(),
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fail_create_user_field_unique_already_exist(self):
        url = reverse('users-list')
        data = {
            'password': 'Belgrano1905',
            'password2': 'Belgrano1905',
            'first_name': self.first_name(),
            'last_name': self.last_name(),
            'username': self.username(),
            'email': self.email(),
        }
        response = self.client.post(
            path=url,
            data=data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response2 = self.client.post(
            path=url,
            data=data,
            format='json',
        )

        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fail_list_not_allowed(self):
        url = reverse('users-list')

        response = self.client.get(url)

        self.assertEqual(response.status_code,
                         status.HTTP_401_UNAUTHORIZED)

    def test_fail_partial_update(self):

        user = self.create_active_user()
        url = reverse('users-detail',
                      kwargs={'username': user.username})

        response = self.client.patch(
            url,
            {'first_name': 'Arty'}
        )

        self.assertEqual(response.status_code,
                         status.HTTP_401_UNAUTHORIZED)


class AuthUserTestCase(RegularUserAPITest, UserFactory):

    def test_get_user(self):
        url = reverse('users-detail',
                      kwargs={'username': self.user.username})

        response = self.client.get(
            url,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_user(self):
        url = reverse('users-detail',
                      kwargs={'username': self.user.username})

        response = self.client.patch(
            url,
            {'first_name': 'Arty'}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(username=self.user.username)

        self.assertTrue(user.first_name == 'Arty')

    def test_fail_update_other_user(self):
        url = reverse('users-list')

        response = self.client.post(
            path=url,
            data={
                'password': 'Belgrano1905',
                'password2': 'Belgrano1905',
                'first_name': self.first_name(),
                'last_name': self.last_name(),
                'username': 'test_to_upd',
                'email': self.email(),
                'is_active': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url2 = reverse('users-detail', kwargs={'username': 'test_to_upd'})
        response = self.client.patch(
            url2,
            {'first_name': 'Arty'}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_user(self):
        url = reverse('users-detail',
                      kwargs={'username': self.user.username})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user = User.objects.get(username=self.user.username)

        self.assertFalse(user.is_active)


class AdminUserListAPITest(AdminUserAPITest):
    def test_users_list(self):

        url = reverse('users-list')

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_users_list_not_found(self):

        url = reverse('users-list')

        response = self.client.get(url, {'search': 'Jejejjeje algooloco'})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
