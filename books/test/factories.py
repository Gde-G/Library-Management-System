import random
import datetime
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from faker import Faker
from faker.providers import BaseProvider
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Author, Genre, Publisher

faker = Faker()


class ImageProvider(BaseProvider):
    def image(self, width=640, height=480):
        image = Image.new('RGB', (width, height), 'rgb(255, 255, 255)')
        stream = BytesIO()
        image.save(stream, format='JPEG')

        filename = f"{faker.word() + str(random.randint(0, 1000))}.jpg"

        image_file = InMemoryUploadedFile(
            stream,
            None,
            filename,
            'image/jpeg',
            stream.getbuffer().nbytes,
            None
        )
        return image_file


faker.add_provider(ImageProvider)


class AuthorFactory:

    def first_name(self):
        first_name = faker.first_name()
        if len(first_name) >= 100:
            first_name = first_name[:98]

        return first_name

    def last_name(self):
        last_name = faker.last_name()
        if len(last_name) >= 100:
            last_name = last_name[:98]

        return last_name

    def nationality(self):
        return faker.country()

    def dates(self):
        birth_date = faker.date_of_birth(minimum_age=15, maximum_age=80)

        death_date = faker.date_between_dates(
            date_start=birth_date, date_end=datetime.date.today())

        birth_date_str = birth_date.strftime("%Y-%m-%d")
        death_date_str = death_date.strftime("%Y-%m-%d")

        return birth_date_str, death_date_str

    def biography(self):
        return faker.paragraph(nb_sentences=5)

    def picture(self):
        return faker.image()


class GenreFactory:
    def name_genre(self):
        return faker.sentence(nb_words=random.randint(2, 10))

    def description(self):
        return faker.paragraph(nb_sentences=5)


class PublisherFactory:
    def name_publisher(self):
        return faker.sentence(nb_words=random.randint(1, 5))

    def country(self):
        return faker.country()


class BookFactory(AuthorFactory, GenreFactory, PublisherFactory):
    def title(self):
        return faker.sentence(nb_words=random.randint(1, 6))

    def author(self):
        dates = self.dates()
        picture_img_data = self.picture().file.getvalue()

        picture_img_file = SimpleUploadedFile(
            'picture_img.jpg', picture_img_data, content_type='image/jpeg')

        return Author.objects.create(
            first_name=self.first_name(),
            last_name=self.last_name(),
            nationality=self.nationality(),
            birth_date=dates[0],
            death_date=dates[1],
            biography=self.biography(),
            picture=picture_img_file
        )

    def language(self):
        return faker.language_code()

    def genre(self):
        return Genre.objects.create(
            name=self.name_genre(),
            description=self.description()
        )

    def publisher(self):
        return Publisher.objects.create(
            name=self.name_publisher(),
            country=self.country()
        )

    def edition(self):
        return random.randint(1, 7)

    def amount_pages(self):
        return random.randint(50, 1100)

    def cover(self):
        return faker.image()

    def publication_date(self):
        return faker.date_between(start_date=datetime.date(1900, 1, 1))
