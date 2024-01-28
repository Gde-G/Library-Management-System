import pdb
import re
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from core.test.test_setup import AdminUserAPITest

from .factories import GenreFactory
from ..models import Genre


class AdminCreateGenreAPITest(AdminUserAPITest, GenreFactory):
    def test_create_genre_needy_fields(self):
        data = {
            'name': self.name_genre()
        }

        url = reverse('genre-list')
        response = self.client.post(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Genre.objects.filter(name=data['name']).exists())

    def test_create_genre_all_fields(self):
        data = {
            'name': self.name_genre(),
            'description': self.description()
        }

        url = reverse('genre-list')
        response = self.client.post(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Genre.objects.filter(name=data['name']).exists())

    def test_crete_genre_fail_not_parse_needy_fields(self):
        data = {
            'description': self.description()
        }
        url = reverse('genre-list')
        response = self.client.post(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AnyListGenreAPITest(APITestCase, GenreFactory):
    def test_list_genre(self):
        for _ in range(3):
            Genre.objects.create(
                name=self.name_genre(),
                description=self.description()
            )

        url = reverse('genre-list')
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 3)

    def test_list_genre_with_search(self):
        for i in range(3):
            if i % 2 == 0:
                name = self.name_genre() + ' memo'
            else:
                name = self.name_genre()

            Genre.objects.create(
                name=name,
                description=self.description()
            )

        url = reverse('genre-list')
        response = self.client.get(
            url,
            {'search': 'memo'}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)

    def test_list_genre_search_not_found(self):
        for _ in range(3):
            Genre.objects.create(
                name=self.name_genre(),
                description=self.description()
            )

        url = reverse('genre-list')
        response = self.client.get(
            url,
            {'search': 'ArtyLocoMoisoman'}
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_genre_paginator(self):

        for _ in range(10):
            Genre.objects.create(
                name=self.name_genre(),
                description=self.description()
            )

        url = reverse('genre-list')
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 10)
        self.assertEqual(len(response.data['results']), 3)
        self.assertIsNotNone(response.data['next'])

    def test_list_genre_paginator_with_search(self):

        for i in range(0, 20):
            if i % 2 == 0:
                name = self.name_genre() + ' artylugio'
            else:
                name = self.name_genre()

            Genre.objects.create(
                name=name,
                description=self.description()
            )

        url = reverse('genre-list')
        response = self.client.get(
            url,
            {'search': 'artylugio'}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 10)
        self.assertEqual(len(response.data['results']), 3)
        self.assertIsNotNone(response.data['next'])

        self.assertTrue(
            bool(
                re.search('search=arty', response.data['next'])
            )
        )


class AnyRetrieveGenreAPITest(APITestCase, GenreFactory):
    def test_retrieve_genre(self):
        genre = Genre.objects.create(
            name=self.name_genre(),
            description=self.description()
        )

        url = reverse('genre-detail', kwargs={'slug': genre.slug})
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], genre.name)

    def test_retrieve_genre_fail_not_found(self):
        url = reverse('genre-detail', kwargs={'slug': 'momo-momom-moomo'})

        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_genre_fail_slug_not_send(self):
        url = reverse('genre-detail', kwargs={'slug': None})

        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AdminUpdateGenreAPITest(AdminUserAPITest, GenreFactory):

    def test_update_genre_with_put_fail(self):
        genre = Genre.objects.create(
            name=self.name_genre(),
            description=self.description()
        )
        old_slug = genre.slug
        data = {
            "name": 'Mystery',
            "description": 'Mystery is a fiction genre where the nature of an event, usually a murder or other crime, remains mysterious until the end of the story.'
        }

        url = reverse('genre-detail', kwargs={'slug': genre.slug})
        response = self.client.put(
            url,
            data
        )

        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_genre_with_patch(self):
        genre = Genre.objects.create(
            name=self.name_genre(),
            description=self.description()
        )
        old_slug = genre.slug
        data = {
            "name": 'Mystery',
            "description": 'Mystery is a fiction genre where the nature of an event, usually a murder or other crime, remains mysterious until the end of the story.'
        }

        url = reverse('genre-detail', kwargs={'slug': genre.slug})
        response = self.client.patch(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        genre.refresh_from_db()

        self.assertEqual(genre.name, data['name'])
        self.assertEqual(genre.description, data['description'])
        self.assertNotEqual(genre.slug, old_slug)

    def test_update_genre_fail_not_found(self):

        data = {
            "name": 'Mystery',
            "description": 'Mystery is a fiction genre where the nature of an event, usually a murder or other crime, remains mysterious until the end of the story.'
        }

        url = reverse('genre-detail', kwargs={'slug': 'monfofofof-fofo'})
        response = self.client.patch(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AdminDeleteGenreAPITest(AdminUserAPITest, GenreFactory):

    def test_delete_genre(self):
        genre = Genre.objects.create(
            name=self.name_genre(),
            description=self.description()
        )
        url = reverse('genre-detail', kwargs={'slug': genre.slug})
        response = self.client.delete(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Genre.objects.all().count(), 0)

    def test_delete_genre_not_found(self):
        url = reverse('genre-detail', kwargs={'slug': ' genre-slug'})
        response = self.client.delete(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
