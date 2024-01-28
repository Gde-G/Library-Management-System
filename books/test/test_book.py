import pdb

from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from core.test.test_setup import AdminUserAPITest

from .factories import BookFactory
from ..models import Book


class AdminCreateBookAPITest(AdminUserAPITest, BookFactory):
    def test_create_book_needy_fields(self):
        cover_img_data = self.cover().file.getvalue()

        cover_img_file = SimpleUploadedFile(
            'cover_img.jpg', cover_img_data, content_type='image/jpeg')
        data = {
            'title': self.title(),
            'author': self.author().id,
            'language': self.language(),
            'genre': self.genre().id,
            'cover': cover_img_file,
            'publication_date': self.publication_date(),
        }

        url = reverse('book-list')
        response = self.client.post(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Book.objects.filter(title=data['title']).exists())

    def test_create_book_all_fields(self):
        cover_img_data = self.cover().file.getvalue()

        cover_img_file = SimpleUploadedFile(
            'cover_img.jpg', cover_img_data, content_type='image/jpeg')
        data = {
            'title': self.title(),
            'author': self.author().id,
            'language': self.language(),
            'genre': self.genre().id,
            'publisher': self.publisher().id,
            'edition': self.edition(),
            'amount_pages': self.amount_pages(),
            'cover': cover_img_file,
            'publication_date': self.publication_date(),

        }

        url = reverse('book-list')
        response = self.client.post(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Book.objects.filter(title=data['title']).exists())

    def test_create_book_fail_not_found_author(self):
        cover_img_data = self.cover().file.getvalue()

        cover_img_file = SimpleUploadedFile(
            'cover_img.jpg', cover_img_data, content_type='image/jpeg')
        data = {
            'title': self.title(),
            'author': 350,
            'language': self.language(),
            'genre': self.genre().id,
            'cover': cover_img_file,
            'publication_date': self.publication_date(),
        }

        url = reverse('book-list')
        response = self.client.post(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('author', response.data.keys())

    def test_create_book_fail_not_found_genre(self):
        cover_img_data = self.cover().file.getvalue()

        cover_img_file = SimpleUploadedFile(
            'cover_img.jpg', cover_img_data, content_type='image/jpeg')
        data = {
            'title': self.title(),
            'author': self.author(),
            'language': self.language(),
            'genre': 350,
            'cover': cover_img_file,
            'publication_date': self.publication_date(),
        }

        url = reverse('book-list')
        response = self.client.post(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('genre', response.data.keys())

    def test_create_book_fail_not_found_publisher(self):
        cover_img_data = self.cover().file.getvalue()

        cover_img_file = SimpleUploadedFile(
            'cover_img.jpg', cover_img_data, content_type='image/jpeg')
        data = {
            'title': self.title(),
            'author': self.author(),
            'language': self.language(),
            'genre': self.genre().id,
            'publisher': 350,
            'cover': cover_img_file,
            'publication_date': self.publication_date(),
        }

        url = reverse('book-list')
        response = self.client.post(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('publisher', response.data.keys())

    def test_create_book_fail_publication_in_future(self):
        cover_img_data = self.cover().file.getvalue()

        cover_img_file = SimpleUploadedFile(
            'cover_img.jpg', cover_img_data, content_type='image/jpeg')
        data = {
            'title': self.title(),
            'author': self.author().id,
            'language': self.language(),
            'genre': self.genre().id,
            'publisher': self.publisher().id,
            'cover': cover_img_file,
            'publication_date': '2025-02-03',
        }

        url = reverse('book-list')
        response = self.client.post(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('publication_date', response.data.keys())

    def test_create_book_fail_multifields_errors(self):
        cover_img_data = self.cover().file.getvalue()

        cover_img_file = SimpleUploadedFile(
            'cover_img.jpg', cover_img_data, content_type='image/jpeg')
        data = {
            'title': self.title(),
            'author': 350,
            'language': self.language(),
            'genre': 450,
            'publisher': 550,
            'cover': cover_img_file,
            'publication_date': '2025-02-03',
        }

        url = reverse('book-list')
        response = self.client.post(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('author', response.data.keys())
        self.assertIn('genre', response.data.keys())
        self.assertIn('publisher', response.data.keys())
        self.assertIn('publication_date', response.data.keys())


class AnyListBooksAPITest(APITestCase, BookFactory):
    def test_list_books(self):
        for _ in range(3):
            cover_img_data = self.cover().file.getvalue()
            cover_img_file = SimpleUploadedFile(
                'cover_img.jpg', cover_img_data, content_type='image/jpeg')

            Book.objects.create(
                title=self.title(),
                author=self.author(),
                language=self.language(),
                genre=self.genre(),
                publisher=self.publisher(),
                amount_pages=self.amount_pages(),
                edition=self.edition(),
                publication_date=self.publication_date(),
                cover=cover_img_file,
            )

        url = reverse('book-list')
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 3)

    def test_list_books_with_search(self):
        for i in range(6):
            cover_img_data = self.cover().file.getvalue()
            cover_img_file = SimpleUploadedFile(
                'cover_img.jpg', cover_img_data, content_type='image/jpeg')

            if i % 2 == 0:
                title = 'artylogico ' + self.title()
            else:
                title = self.title()
            Book.objects.create(
                title=title,
                author=self.author(),
                language=self.language(),
                genre=self.genre(),
                publisher=self.publisher(),
                amount_pages=self.amount_pages(),
                edition=self.edition(),
                publication_date=self.publication_date(),
                cover=cover_img_file,
            )

        url = reverse('book-list')
        response = self.client.get(
            url,
            {'search': 'artylogico'}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 3)

        for res in response.data['results']:
            self.assertIn('artylogico', res['title'])

    def test_list_books_pagination(self):
        for _ in range(6):
            cover_img_data = self.cover().file.getvalue()
            cover_img_file = SimpleUploadedFile(
                'cover_img.jpg', cover_img_data, content_type='image/jpeg')

            Book.objects.create(
                title=self.title(),
                author=self.author(),
                language=self.language(),
                genre=self.genre(),
                publisher=self.publisher(),
                amount_pages=self.amount_pages(),
                edition=self.edition(),
                publication_date=self.publication_date(),
                cover=cover_img_file,
            )

        url = reverse('book-list')
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 6)
        self.assertIsNotNone(response.data['next'])

    def test_list_books_pagination_with_search(self):
        for i in range(12):
            cover_img_data = self.cover().file.getvalue()
            cover_img_file = SimpleUploadedFile(
                'cover_img.jpg', cover_img_data, content_type='image/jpeg')

            if i % 2 == 0:
                title = 'artylogico ' + self.title()
            else:
                title = self.title()
            Book.objects.create(
                title=title,
                author=self.author(),
                language=self.language(),
                genre=self.genre(),
                publisher=self.publisher(),
                amount_pages=self.amount_pages(),
                edition=self.edition(),
                publication_date=self.publication_date(),
                cover=cover_img_file,
            )

        url = reverse('book-list')
        response = self.client.get(
            url,
            {'search': 'artylogico'}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 6)

        for res in response.data['results']:
            self.assertIn('artylogico', res['title'])

        self.assertIsNotNone(response.data['next'])

    def test_list_books_fails_not_found(self):
        url = reverse('book-list')
        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_books_fails_not_found_with_search(self):
        for _ in range(6):
            cover_img_data = self.cover().file.getvalue()
            cover_img_file = SimpleUploadedFile(
                'cover_img.jpg', cover_img_data, content_type='image/jpeg')

            Book.objects.create(
                title=self.title(),
                author=self.author(),
                language=self.language(),
                genre=self.genre(),
                publisher=self.publisher(),
                amount_pages=self.amount_pages(),
                edition=self.edition(),
                publication_date=self.publication_date(),
                cover=cover_img_file,
            )
        url = reverse('book-list')
        response = self.client.get(
            url,
            {'search': 'Belgrano Campeon'}
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AnyRetrieveBookAPITest(APITestCase, BookFactory):
    def test_retrieve_book(self):
        cover_img_data = self.cover().file.getvalue()
        cover_img_file = SimpleUploadedFile(
            'cover_img.jpg', cover_img_data, content_type='image/jpeg')

        book = Book.objects.create(
            title=self.title(),
            author=self.author(),
            language=self.language(),
            genre=self.genre(),
            publisher=self.publisher(),
            amount_pages=self.amount_pages(),
            edition=self.edition(),
            publication_date=self.publication_date(),
            cover=cover_img_file,
        )

        url = reverse('book-detail', kwargs={'slug': book.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(book.slug, response.data['slug'])

    def test_retrieve_book_fail_not_found(self):
        url = reverse('book-detail', kwargs={'slug': 'mongold-soso-lala'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AdminUpdateBookAPITest(AdminUserAPITest, BookFactory):

    def test_update_fail_put_method(self):
        url = reverse('book-detail', kwargs={'slug': 'book-random'})

        response = self.client.put(
            url
        )

        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_needy_fields(self):
        cover_img_data = self.cover().file.getvalue()
        cover_img_file = SimpleUploadedFile(
            'cover_img.jpg', cover_img_data, content_type='image/jpeg')

        book = Book.objects.create(
            title=self.title(),
            author=self.author(),
            language=self.language(),
            genre=self.genre(),
            publisher=self.publisher(),
            amount_pages=self.amount_pages(),
            edition=self.edition(),
            publication_date=self.publication_date(),
            cover=cover_img_file,
        )
        old_slug = book.slug
        data = {
            'title': 'Maldicion va a ser un dia hermoso',
            'author': self.author().id,
            'language': 'Español',
            'genre': self.genre().id,
            'publication_date': '1985-02-05',
        }
        url = reverse('book-detail', kwargs={'slug': old_slug})
        response = self.client.patch(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        book.refresh_from_db()

        self.assertNotEqual(old_slug, book.slug)
        self.assertEqual(data['title'], book.title)
        self.assertEqual(data['author'], book.author.id)
        self.assertEqual(data['genre'], book.genre.id)
        self.assertEqual(data['language'], book.language)
        self.assertEqual(data['publication_date'],
                         book.publication_date.strftime('%Y-%m-%d'))

    def test_update_all_fields(self):
        cover_img_data = self.cover().file.getvalue()
        cover_img_file = SimpleUploadedFile(
            'cover_img.jpg', cover_img_data, content_type='image/jpeg')

        cover_img_data2 = self.cover().file.getvalue()
        cover_img_file2 = SimpleUploadedFile(
            'cover_img2.jpg', cover_img_data2, content_type='image/jpeg')

        book = Book.objects.create(
            title=self.title(),
            author=self.author(),
            language=self.language(),
            genre=self.genre(),
            publisher=self.publisher(),
            amount_pages=self.amount_pages(),
            edition=self.edition(),
            publication_date=self.publication_date(),
            cover=cover_img_file,
        )
        old_slug = book.slug
        data = {
            'title': 'Maldicion va a ser un dia hermoso',
            'author': self.author().id,
            'language': 'Español',
            'genre': self.genre().id,
            'publisher': self.publisher().id,
            'publication_date': '1985-02-05',
            'cover': cover_img_file2,
            'amount_pages': 233,
            'edition': 4,
        }
        url = reverse('book-detail', kwargs={'slug': old_slug})
        response = self.client.patch(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        book.refresh_from_db()

        self.assertNotEqual(old_slug, book.slug)
        self.assertEqual(data['title'], book.title)
        self.assertEqual(data['author'], book.author.id)
        self.assertEqual(data['genre'], book.genre.id)
        self.assertEqual(data['language'], book.language)
        self.assertEqual(data['publisher'], book.publisher.id)
        self.assertEqual(data['edition'], book.edition)
        self.assertEqual(data['amount_pages'], book.amount_pages)
        self.assertEqual(data['publication_date'],
                         book.publication_date.strftime('%Y-%m-%d'))

    def test_update_single_field(self):
        cover_img_data = self.cover().file.getvalue()
        cover_img_file = SimpleUploadedFile(
            'cover_img.jpg', cover_img_data, content_type='image/jpeg')

        book = Book.objects.create(
            title=self.title(),
            author=self.author(),
            language=self.language(),
            genre=self.genre(),
            publisher=self.publisher(),
            amount_pages=self.amount_pages(),
            edition=self.edition(),
            publication_date=self.publication_date(),
            cover=cover_img_file,
        )
        old_slug = book.slug
        data = {

        }
        url = reverse('book-detail', kwargs={'slug': old_slug})
        response = self.client.patch(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        book.refresh_from_db()

    def test_update_fail_foreignkeys_not_exists(self):
        cover_img_data = self.cover().file.getvalue()
        cover_img_file = SimpleUploadedFile(
            'cover_img.jpg', cover_img_data, content_type='image/jpeg')

        book = Book.objects.create(
            title=self.title(),
            author=self.author(),
            language=self.language(),
            genre=self.genre(),
            publisher=self.publisher(),
            amount_pages=self.amount_pages(),
            edition=self.edition(),
            publication_date=self.publication_date(),
            cover=cover_img_file,
        )
        old_slug = book.slug
        data = {
            'author': 2312,
            'genre': 2312,
            'publisher': 2312
        }
        url = reverse('book-detail', kwargs={'slug': old_slug})
        response = self.client.patch(
            url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('author', response.data.keys())
        self.assertIn('genre', response.data.keys())
        self.assertIn('publisher', response.data.keys())


class AdminDeleteBookAPITest(AdminUserAPITest, BookFactory):
    def test_delete_book(self):
        cover_img_data = self.cover().file.getvalue()
        cover_img_file = SimpleUploadedFile(
            'cover_img.jpg', cover_img_data, content_type='image/jpeg')

        book = Book.objects.create(
            title=self.title(),
            author=self.author(),
            language=self.language(),
            genre=self.genre(),
            publisher=self.publisher(),
            amount_pages=self.amount_pages(),
            edition=self.edition(),
            publication_date=self.publication_date(),
            cover=cover_img_file,
        )
        slug = book.slug
        url = reverse('book-detail', kwargs={'slug': slug})
        response = self.client.delete(
            url
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Book.objects.filter(slug=slug).exists())

    def test_delete_book_fail_not_found(self):
        url = reverse('book-detail', kwargs={'slug': 'slug-moky'})
        response = self.client.delete(
            url
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AnyListBookByAuthor(APITestCase, BookFactory):
    def test_list_books_by_author(self):
        author = self.author()
        for i in range(6):
            cover_img_data = self.cover().file.getvalue()
            cover_img_file = SimpleUploadedFile(
                'cover_img.jpg', cover_img_data, content_type='image/jpeg')

            if i % 2 == 0:
                author_book = author
            else:
                author_book = self.author()
            Book.objects.create(
                title=self.title(),
                author=author_book,
                language=self.language(),
                genre=self.genre(),
                publisher=self.publisher(),
                amount_pages=self.amount_pages(),
                edition=self.edition(),
                publication_date=self.publication_date(),
                cover=cover_img_file,
            )

        url = reverse('book-list-by-author', kwargs={'pk': author.id})

        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertIsNone(response.data['next'])

    def test_list_books_by_author_paginated(self):
        author = self.author()
        for i in range(20):
            cover_img_data = self.cover().file.getvalue()
            cover_img_file = SimpleUploadedFile(
                'cover_img.jpg', cover_img_data, content_type='image/jpeg')

            if i % 2 == 0:
                author_book = author
            else:
                author_book = self.author()
            Book.objects.create(
                title=self.title(),
                author=author_book,
                language=self.language(),
                genre=self.genre(),
                publisher=self.publisher(),
                amount_pages=self.amount_pages(),
                edition=self.edition(),
                publication_date=self.publication_date(),
                cover=cover_img_file,
            )

        url = reverse('book-list-by-author', kwargs={'pk': author.id})

        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 10)
        self.assertIsNotNone(response.data['next'])

    def test_list_books_by_author_pk_not_digit(self):
        url = reverse('book-list-by-author', kwargs={'pk': 'mongo'})
        response = self.client.get(
            url
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_books_by_author_not_found(self):
        url = reverse('book-list-by-author', kwargs={'pk': 2222})
        response = self.client.get(
            url
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AnyListBookByGenre(APITestCase, BookFactory):
    def test_list_books_by_genre(self):
        genre = self.genre()
        for i in range(6):
            cover_img_data = self.cover().file.getvalue()
            cover_img_file = SimpleUploadedFile(
                'cover_img.jpg', cover_img_data, content_type='image/jpeg')

            if i % 2 == 0:
                genre_book = genre
            else:
                genre_book = self.genre()
            Book.objects.create(
                title=self.title(),
                genre=genre_book,
                language=self.language(),
                author=self.author(),
                publisher=self.publisher(),
                amount_pages=self.amount_pages(),
                edition=self.edition(),
                publication_date=self.publication_date(),
                cover=cover_img_file,
            )

        url = reverse('book-list-by-genre', kwargs={'slug': genre.slug})

        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertIsNone(response.data['next'])

    def test_list_books_by_genre_paginated(self):
        genre = self.genre()
        for i in range(20):
            cover_img_data = self.cover().file.getvalue()
            cover_img_file = SimpleUploadedFile(
                'cover_img.jpg', cover_img_data, content_type='image/jpeg')

            if i % 2 == 0:
                genre_book = genre
            else:
                genre_book = self.genre()
            Book.objects.create(
                title=self.title(),
                genre=genre_book,
                language=self.language(),
                author=self.author(),
                publisher=self.publisher(),
                amount_pages=self.amount_pages(),
                edition=self.edition(),
                publication_date=self.publication_date(),
                cover=cover_img_file,
            )

        url = reverse('book-list-by-genre', kwargs={'slug': genre.slug})

        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 10)
        self.assertIsNotNone(response.data['next'])

    def test_list_books_by_genre_slug_invalid(self):
        url = reverse('book-list-by-genre', kwargs={'slug': ' '})
        response = self.client.get(
            url
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_books_by_genre_not_found(self):
        url = reverse('book-list-by-genre', kwargs={'slug': 'mongo-mencion'})
        response = self.client.get(
            url
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AnyListBookByPublisher(APITestCase, BookFactory):
    def test_list_books_by_publisher(self):
        publisher = self.publisher()
        for i in range(6):
            cover_img_data = self.cover().file.getvalue()
            cover_img_file = SimpleUploadedFile(
                'cover_img.jpg', cover_img_data, content_type='image/jpeg')

            if i % 2 == 0:
                publisher_book = publisher
            else:
                publisher_book = self.publisher()
            Book.objects.create(
                title=self.title(),
                publisher=publisher_book,
                language=self.language(),
                genre=self.genre(),
                author=self.author(),
                amount_pages=self.amount_pages(),
                edition=self.edition(),
                publication_date=self.publication_date(),
                cover=cover_img_file,
            )

        url = reverse('book-list-by-publisher', kwargs={'pk': publisher.id})

        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertIsNone(response.data['next'])

    def test_list_books_by_publisher_paginated(self):
        publisher = self.publisher()
        for i in range(20):
            cover_img_data = self.cover().file.getvalue()
            cover_img_file = SimpleUploadedFile(
                'cover_img.jpg', cover_img_data, content_type='image/jpeg')

            if i % 2 == 0:
                publisher_book = publisher
            else:
                publisher_book = self.publisher()
            Book.objects.create(
                title=self.title(),
                publisher=publisher_book,
                language=self.language(),
                genre=self.genre(),
                author=self.author(),
                amount_pages=self.amount_pages(),
                edition=self.edition(),
                publication_date=self.publication_date(),
                cover=cover_img_file,
            )

        url = reverse('book-list-by-publisher', kwargs={'pk': publisher.id})

        response = self.client.get(
            url
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 10)
        self.assertIsNotNone(response.data['next'])

    def test_list_books_by_publisher_pk_not_digit(self):
        url = reverse('book-list-by-publisher', kwargs={'pk': 'mongo'})
        response = self.client.get(
            url
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_books_by_publisher_not_found(self):
        url = reverse('book-list-by-publisher', kwargs={'pk': 2222})
        response = self.client.get(
            url
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
