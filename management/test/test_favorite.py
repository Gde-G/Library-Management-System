import pdb

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.test.test_setup import RegularUserAPITest
from .factories import FavoriteFactory
from ..models import Favorite


class AuthCreateFavoriteAPITest(RegularUserAPITest, FavoriteFactory):
    def test_create_favorite(self):
        book = self.book()

        data = {
            'book': book.slug
        }
        url = reverse('fav-list')
        response = self.client.post(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Favorite.objects.filter(
            book=book, user=self.user).exists())

    def test_create_favorite_fail_book_not_found(self):
        data = {
            'book': 'jeje-lolo-jejeje'
        }
        url = reverse('fav-list')
        response = self.client.post(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('book', response.data)

    def test_create_favorite_fail_already_exists(self):
        book = self.book()

        data = {
            'book': book.slug
        }
        url = reverse('fav-list')
        response = self.client.post(
            url,
            data
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response2 = self.client.post(
            url,
            data
        )
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('fav', response2.data)


class AuthListFavoriteAPITest(RegularUserAPITest, FavoriteFactory):
    def test_list_favorites(self):
        for _ in range(3):
            book = self.book()

            Favorite.objects.create(
                user=self.user,
                book=book
            )

            book = None

        url = reverse('fav-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 3)

    def test_list_favorites_paginator(self):
        for _ in range(6):
            book = self.book()

            Favorite.objects.create(
                user=self.user,
                book=book
            )

            book = None

        url = reverse('fav-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 6)
        self.assertEqual(len(response.data['results']), 3)
        self.assertIsNotNone(response.data['next'])

    def test_list_favorites_not_found(self):
        url = reverse('fav-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AuthDeleteFavoriteAPITest(RegularUserAPITest, FavoriteFactory):
    def test_delete_fav(self):
        book = self.book()

        Favorite.objects.create(
            user=self.user,
            book=book
        )

        url = reverse('fav-detail', kwargs={'book': book.slug})
        response = self.client.delete(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_fav_fail_book_not_found(self):
        url = reverse('fav-detail', kwargs={'book': 'jeje-momojeje-je'})
        response = self.client.delete(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
