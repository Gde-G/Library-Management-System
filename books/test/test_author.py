import pdb
import datetime
from django.urls import reverse

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from core.test.test_setup import AdminUserAPITest

from .factories import AuthorFactory
from ..models import Author


class AdminCreateAuthorAPITest(AdminUserAPITest, AuthorFactory):

    def test_create_author_needy_fields(self):
        url = reverse('author-list')
        picture_img_data = self.picture().file.getvalue()

        picture_img_file = SimpleUploadedFile(
            'picture_img.jpg', picture_img_data, content_type='image/jpeg')
        birth_date = self.dates()[0]

        response = self.client.post(
            path=url,
            data={
                'first_name': self.first_name(),
                'last_name': self.last_name(),
                'biography': self.biography(),
                'birth_date': birth_date,
                'picture': picture_img_file,
            },
        )

        created_author = Author.objects.first()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual('', created_author.picture)

    def test_create_author_all_fields(self):
        url = reverse('author-list')
        picture_img_data = self.picture().file.getvalue()

        picture_img_file = SimpleUploadedFile(
            'picture_img.jpg', picture_img_data, content_type='image/jpeg'),
        dates = self.dates()

        response = self.client.post(
            path=url,
            data={
                'first_name': self.first_name(),
                'last_name': self.last_name(),
                'nationality': self.nationality(),
                'biography': self.biography(),
                'birth_date': dates[0],
                'death_date': dates[1],
                'picture': picture_img_file,
            },
        )

        created_author = Author.objects.first()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual('', created_author.picture)

    def test_create_author_fail_missing_needy_field(self):
        url = reverse('author-list')
        picture_img_data = self.picture().file.getvalue()

        picture_img_file = SimpleUploadedFile(
            'picture_img.jpg', picture_img_data, content_type='image/jpeg'),
        birth_date = self.dates()[0]

        response = self.client.post(
            path=url,
            data={
                'first_name': self.first_name(),
                'last_name': self.last_name(),
                'biography': self.biography(),

                'picture': picture_img_file,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('birth_date' in response.data.keys())

    def test_create_author_fail_die_before_born(self):
        url = reverse('author-list')
        picture_img_data = self.picture().file.getvalue()

        picture_img_file = SimpleUploadedFile(
            'picture_img.jpg', picture_img_data, content_type='image/jpeg'),

        response = self.client.post(
            path=url,
            data={
                'first_name': self.first_name(),
                'last_name': self.last_name(),
                'nationality': self.nationality(),
                'biography': self.biography(),
                'birth_date': datetime.date(year=2001, month=4, day=19),
                'death_date': datetime.date(year=2000, month=4, day=19),
                'picture': picture_img_file,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('death_date' in response.data.keys())

    def test_create_author_fail_born_future_date(self):
        url = reverse('author-list')
        picture_img_data = self.picture().file.getvalue()

        picture_img_file = SimpleUploadedFile(
            'picture_img.jpg', picture_img_data, content_type='image/jpeg'),

        response = self.client.post(
            path=url,
            data={
                'first_name': self.first_name(),
                'last_name': self.last_name(),
                'nationality': self.nationality(),
                'biography': self.biography(),
                'birth_date': datetime.date(year=2024, month=12, day=29),
                'picture': picture_img_file,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('birth_date' in response.data.keys())


class AnyListAuthorAPITest(APITestCase, AuthorFactory):
    def test_list_authors(self):
        for _ in range(3):
            dates = self.dates()
            picture_img_data = self.picture().file.getvalue()
            picture_img_file = SimpleUploadedFile(
                'picture_img.jpg', picture_img_data, content_type='image/jpeg')

            Author.objects.create(
                first_name=self.first_name(),
                last_name=self.last_name(),
                nationality=self.nationality(),
                biography=self.biography(),
                birth_date=dates[0],
                death_date=dates[1],
                picture=picture_img_file
            )

            dates = []
            picture_img_data = None
            picture_img_file = None

        url = reverse('author-list')

        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 3)

    def test_list_authors_search_first_name(self):
        for i in range(6):
            dates = self.dates()
            picture_img_data = self.picture().file.getvalue()
            picture_img_file = SimpleUploadedFile(
                'picture_img.jpg', picture_img_data, content_type='image/jpeg')

            if i % 2 == 0:
                Author.objects.create(
                    first_name=self.first_name() + "hum",
                    last_name=self.last_name(),
                    nationality=self.nationality(),
                    biography=self.biography(),
                    birth_date=dates[0],
                    death_date=dates[1],
                    picture=picture_img_file
                )
            else:
                Author.objects.create(
                    first_name=self.first_name(),
                    last_name=self.last_name(),
                    nationality=self.nationality(),
                    biography=self.biography(),
                    birth_date=dates[0],
                    death_date=dates[1],
                    picture=picture_img_file
                )
            dates = []
            picture_img_data = None
            picture_img_file = None

        url = reverse('author-list')

        response = self.client.get(
            url,
            {'search': 'hum'}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 3)

        for res in response.data['results']:
            self.assertTrue('hum' in res['name'])

    def test_list_authors_search_last_name(self):
        for i in range(6):
            dates = self.dates()
            picture_img_data = self.picture().file.getvalue()
            picture_img_file = SimpleUploadedFile(
                'picture_img.jpg', picture_img_data, content_type='image/jpeg')

            if i % 2 == 0:
                Author.objects.create(
                    first_name=self.first_name(),
                    last_name=self.last_name() + "hum",
                    nationality=self.nationality(),
                    biography=self.biography(),
                    birth_date=dates[0],
                    death_date=dates[1],
                    picture=picture_img_file
                )
            else:
                Author.objects.create(
                    first_name=self.first_name(),
                    last_name=self.last_name(),
                    nationality=self.nationality(),
                    biography=self.biography(),
                    birth_date=dates[0],
                    death_date=dates[1],
                    picture=picture_img_file
                )
            dates = []
            picture_img_data = None
            picture_img_file = None

        url = reverse('author-list')

        response = self.client.get(
            url,
            {'search': 'hum'}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 3)

        for res in response.data['results']:
            self.assertTrue('hum' in res['name'])

    def test_list_authors_search_name(self):
        for i in range(6):
            dates = self.dates()
            picture_img_data = self.picture().file.getvalue()
            picture_img_file = SimpleUploadedFile(
                'picture_img.jpg', picture_img_data, content_type='image/jpeg')

            if i % 2 == 0:
                Author.objects.create(
                    first_name=self.first_name() + " ronny",
                    last_name=self.last_name() + " hum",
                    nationality=self.nationality(),
                    biography=self.biography(),
                    birth_date=dates[0],
                    death_date=dates[1],
                    picture=picture_img_file
                )
            else:
                Author.objects.create(
                    first_name=self.first_name(),
                    last_name=self.last_name(),
                    nationality=self.nationality(),
                    biography=self.biography(),
                    birth_date=dates[0],
                    death_date=dates[1],
                    picture=picture_img_file
                )
            dates = []
            picture_img_data = None
            picture_img_file = None

        url = reverse('author-list')

        response = self.client.get(
            url,
            {'search': 'ronny hum'}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 3)

        for res in response.data['results']:
            self.assertTrue('hum' in res['name'] or 'ronny' in res['name'])

    def test_list_authors_not_found(self):
        for _ in range(6):
            dates = self.dates()
            picture_img_data = self.picture().file.getvalue()
            picture_img_file = SimpleUploadedFile(
                'picture_img.jpg', picture_img_data, content_type='image/jpeg')

            Author.objects.create(
                first_name=self.first_name(),
                last_name=self.last_name(),
                nationality=self.nationality(),
                biography=self.biography(),
                birth_date=dates[0],
                death_date=dates[1],
                picture=picture_img_file
            )

            dates = []
            picture_img_data = None
            picture_img_file = None

        url = reverse('author-list')

        response = self.client.get(
            url,
            {'search': 'ronnmoniculicay'}
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_authors_paginator(self):
        for _ in range(10):
            dates = self.dates()
            picture_img_data = self.picture().file.getvalue()
            picture_img_file = SimpleUploadedFile(
                'picture_img.jpg', picture_img_data, content_type='image/jpeg')

            Author.objects.create(
                first_name=self.first_name(),
                last_name=self.last_name(),
                nationality=self.nationality(),
                biography=self.biography(),
                birth_date=dates[0],
                death_date=dates[1],
                picture=picture_img_file
            )

            dates = []
            picture_img_data = None
            picture_img_file = None

        url = reverse('author-list')

        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 10)
        self.assertEqual(len(response.data['results']), 3)
        self.assertIsNotNone(response.data['next'])


class AnyRetrieveAuthorAPITest(APITestCase, AuthorFactory):
    def test_retrieve_author(self):

        picture_img_data = self.picture().file.getvalue()
        picture_img_file = SimpleUploadedFile(
            'picture_img.jpg', picture_img_data, content_type='image/jpeg')
        dates = self.dates()

        author = Author.objects.create(
            first_name=self.first_name(),
            last_name=self.last_name(),
            nationality=self.nationality(),
            biography=self.biography(),
            birth_date=dates[0],
            death_date=dates[1],
            picture=picture_img_file
        )

        url = reverse('author-detail', kwargs={'pk': author.id})
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            author.first_name.capitalize() + ' ' + author.last_name.capitalize(),
            response.data['name']

        )

    def test_retrieve_author_not_found(self):

        url = reverse('author-detail', kwargs={'pk': 5643245})
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_author_pk_not_parse(self):

        url = reverse('author-detail', kwargs={'pk': None})
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AdminUpdateAuthorAPITest(AdminUserAPITest, AuthorFactory):
    def test_update_author_all_fields(self):
        picture_img_data = self.picture().file.getvalue()

        picture_img_file = SimpleUploadedFile(
            'picture_img.jpg', picture_img_data, content_type='image/jpeg')

        dates = self.dates()

        author = Author.objects.create(
            first_name=self.first_name(),
            last_name=self.last_name(),
            nationality=self.nationality(),
            biography=self.biography(),
            birth_date=dates[0],
            death_date=dates[1],
            picture=picture_img_file
        )

        data = {
            'first_name': 'Julio',
            'last_name': 'Cortazar',
            'nationality': 'Argentina',
            'biography': 'Fue un escritor y profesor argentino. También trabajó como traductor, oficio que desempeñó para la Unesco y varias editoriales.',
            'birth_date': '1914-08-26',
            'death_date': '1984-02-12',
        }

        url = reverse('author-detail', kwargs={'pk': author.id})

        response = self.client.patch(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        author.refresh_from_db()

        self.assertEqual(author.first_name, data['first_name'].lower())

    def test_update_author_fail_not_parse_pk(self):

        data = {
            'first_name': 'Julio',
            'last_name': 'Cortazar',
            'nationality': 'Argentina',
            'biography': 'Fue un escritor y profesor argentino. También trabajó como traductor, oficio que desempeñó para la Unesco y varias editoriales.',
            'birth_date': '1914-08-26',
            'death_date': '1984-02-12',
        }

        url = reverse('author-detail', kwargs={'pk': None})

        response = self.client.patch(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_author_fail_not_found(self):
        data = {
            'first_name': 'Julio',
            'last_name': 'Cortazar',
            'nationality': 'Argentina',
            'biography': 'Fue un escritor y profesor argentino. También trabajó como traductor, oficio que desempeñó para la Unesco y varias editoriales.',
            'birth_date': '1914-08-26',
            'death_date': '1984-02-12',
        }

        url = reverse('author-detail', kwargs={'pk': 546321})

        response = self.client.patch(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AdminDeleteAuthorAPITest(AdminUserAPITest, AuthorFactory):
    def test_delete_author(self):
        dates = self.dates()
        picture_img_data = self.picture().file.getvalue()
        picture_img_file = SimpleUploadedFile(
            'picture_img.jpg', picture_img_data, content_type='image/jpeg')

        author = Author.objects.create(
            first_name=self.first_name(),
            last_name=self.last_name(),
            nationality=self.nationality(),
            biography=self.biography(),
            birth_date=dates[0],
            death_date=dates[1],
            picture=picture_img_file
        )

        url = reverse('author-detail', kwargs={'pk': author.id})

        response = self.client.delete(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Author.objects.filter(id=author.id).exists())

    def test_delete_author_fail_not_parse_pk(self):
        url = reverse('author-detail', kwargs={'pk': None})

        response = self.client.delete(
            url,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_author_fail_not_found(self):

        url = reverse('author-detail', kwargs={'pk': 546321})

        response = self.client.delete(
            url,
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
