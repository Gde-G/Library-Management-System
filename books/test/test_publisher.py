import pdb
import re
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from core.test.test_setup import AdminUserAPITest

from .factories import PublisherFactory
from ..models import Publisher


class AdminCreatePublisher(AdminUserAPITest, PublisherFactory):

    def test_create_publisher(self):
        data = {
            'name': self.name_publisher(),
            'country': self.country()
        }

        url = reverse('publisher-list')
        response = self.client.post(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Publisher.objects.filter(name=data['name']).exists())

    def test_crete_publisher_fail_not_parse_needy_fields(self):
        data = {
            'country': self.country()
        }
        url = reverse('publisher-list')
        response = self.client.post(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AnyListPublisherAPITest(APITestCase, PublisherFactory):
    def test_list_publisher(self):
        for _ in range(3):
            Publisher.objects.create(
                name=self.name_publisher(),
                country=self.country()
            )

        url = reverse('publisher-list')
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 3)

    def test_list_publisher_with_search(self):
        for i in range(3):
            if i % 2 == 0:
                name = self.name_publisher() + ' memo'
            else:
                name = self.name_publisher()

            Publisher.objects.create(
                name=name,
                country=self.country()
            )

        url = reverse('publisher-list')
        response = self.client.get(
            url,
            {'search': 'memo'}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)

    def test_list_publisher_search_not_found(self):
        for _ in range(3):
            Publisher.objects.create(
                name=self.name_publisher(),
                country=self.country()
            )

        url = reverse('publisher-list')
        response = self.client.get(
            url,
            {'search': 'ArtyLocoMoisoman'}
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_publisher_paginator(self):

        for _ in range(10):
            Publisher.objects.create(
                name=self.name_publisher(),
                country=self.country()
            )

        url = reverse('publisher-list')
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 10)
        self.assertEqual(len(response.data['results']), 3)
        self.assertIsNotNone(response.data['next'])

    def test_list_publisher_paginator_with_search(self):

        for i in range(20):
            if i % 2 == 0:
                name = self.name_publisher() + ' arty'
            else:
                name = self.name_publisher()

            Publisher.objects.create(
                name=name,
                country=self.country()
            )

        url = reverse('publisher-list')
        response = self.client.get(
            url,
            {'search': 'arty'}
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


class AnyRetrievePublisherAPITest(APITestCase, PublisherFactory):
    def test_retrieve_publisher(self):
        publisher = Publisher.objects.create(
            name=self.name_publisher(),
            country=self.country()
        )

        url = reverse('publisher-detail', kwargs={'pk': publisher.id})
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], publisher.name)

    def test_retrieve_publisher_fail_not_found(self):
        url = reverse('publisher-detail', kwargs={'pk': 'momo-momom-moomo'})

        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_publisher_fail_id_not_send(self):
        url = reverse('publisher-detail', kwargs={'pk': None})

        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AdminUpdatePublisherAPITest(AdminUserAPITest, PublisherFactory):

    def test_update_publisher_with_put_fail(self):
        publisher = Publisher.objects.create(
            name=self.name_publisher(),
            country=self.country()
        )

        data = {
            "name": 'Mystery',
            "country": 'Argentina'
        }

        url = reverse('publisher-detail', kwargs={'pk': publisher.id})
        response = self.client.put(
            url,
            data
        )

        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_publisher_with_patch(self):
        publisher = Publisher.objects.create(
            name=self.name_publisher(),
            country=self.country()
        )

        data = {
            "name": 'Mystery',
            "country": 'Argentina'
        }

        url = reverse('publisher-detail', kwargs={'pk': publisher.id})
        response = self.client.patch(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        publisher.refresh_from_db()

        self.assertEqual(publisher.name, data['name'])
        self.assertEqual(publisher.country, data['country'])

    def test_update_publisher_fail_not_found(self):

        data = {
            "name": 'Mystery',
            "country": 'Argentina'
        }

        url = reverse('publisher-detail', kwargs={'pk': 6546542})
        response = self.client.patch(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AdminDeletePublisherAPITest(AdminUserAPITest, PublisherFactory):

    def test_delete_publisher(self):
        publisher = Publisher.objects.create(
            name=self.name_publisher(),
            country=self.country()
        )
        url = reverse('publisher-detail', kwargs={'pk': publisher.id})
        response = self.client.delete(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Publisher.objects.all().count(), 0)

    def test_delete_publisher_not_found(self):
        url = reverse('publisher-detail', kwargs={'pk': 65424})
        response = self.client.delete(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
