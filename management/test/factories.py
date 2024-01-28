import random
import datetime
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from faker import Faker
from faker.providers import BaseProvider
from django.core.files.uploadedfile import SimpleUploadedFile

from books.models import Book
from books.test.factories import BookFactory
from ..models import Favorite, Reservation

faker = Faker()


class FavoriteFactory(BookFactory):
    def book(self):
        cover_img_data = self.cover().file.getvalue()
        cover_img_file = SimpleUploadedFile(
            'cover_img.jpg', cover_img_data, content_type='image/jpeg')

        return Book.objects.create(
            title=self.title(),
            author=self.author(),
            language=self.language(),
            genre=self.genre(),
            publisher=self.publisher(),
            amount_pages=self.amount_pages(),
            publication_date=self.publication_date(),
            cover=cover_img_file
        )


class ReservationFactory(FavoriteFactory):
    def start_end_dates(self):
        start_date = faker.date_between_dates(
            date_start=datetime.date.today(), date_end=datetime.date.today()+datetime.timedelta(days=30))
        end_date = faker.date_between_dates(
            date_start=start_date, date_end=start_date+datetime.timedelta(days=30))

        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        return start_date_str, end_date_str

    def note(self):
        return faker.paragraph(nb_sentences=2)

    def reservation_success(self, user):
        dates = self.start_end_dates()

        return Reservation.objects.create(
            user=user,
            book=self.book(),
            start_date=dates[0],
            end_date=dates[1],
            initial_price=10.00,
        )

    def reservation_as_data(self, user, book=None, start_date=None, end_date=None, notes=None):
        dates = self.start_end_dates()
        data = {
            'user': user,
            'book': book if book else self.book().slug,
            'start_date': start_date if start_date else dates[0],
            'end_date': end_date if end_date else dates[1],
        }
        if notes:
            data['notes'] = notes

        return data
