from django.db import models
from django.utils.text import slugify

from core.models import DatesRecordsBaseModel


def create_authors_pic_path(instance, filename):
    ext = filename.split('.')[-1]
    first_name = instance.first_name.replace(' ', '_')
    last_name = instance.last_name.replace(' ', '_')
    return f'authors/{first_name}-{last_name}.{ext}'


def create_books_cover_path(instance, filename):
    ext = filename.split('.')[-1]
    title = instance.title.replace(' ', '_')

    return f'books/{title}.{ext}'


class Author(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    nationality = models.CharField(max_length=50, null=True, blank=True)
    birth_date = models.DateField()
    death_date = models.DateField(null=True, blank=True)
    biography = models.TextField()
    picture = models.ImageField(upload_to=create_authors_pic_path)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['first_name', 'last_name']
        verbose_name = 'Author'
        verbose_name_plural = 'Authors'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=160, blank=True, null=True, unique=True)

    def save(self, *args, **kwargs):
        if self.name:
            if not self.slug or self.name != self._meta.model.objects.get(pk=self.pk).name:
                self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Publisher(models.Model):
    name = models.CharField(max_length=200, unique=True)
    country = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Book(DatesRecordsBaseModel):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(
        Author, on_delete=models.CASCADE, null=True, blank=True)
    language = models.CharField(max_length=50)
    genre = models.ForeignKey(Genre, to_field='slug', on_delete=models.CASCADE)
    publisher = models.ForeignKey(
        Publisher, on_delete=models.CASCADE, null=True, blank=True)
    edition = models.PositiveIntegerField(default=1)
    amount_pages = models.PositiveIntegerField(default=1)
    cover = models.ImageField(upload_to=create_books_cover_path)
    publication_date = models.DateField()
    slug = models.SlugField(max_length=250, blank=True, null=True, unique=True)

    def save(self, *args, **kwargs):
        if self.title:
            if not self.slug or self.title != self._meta.model.objects.get(pk=self.pk).title:
                self.slug = slugify(self.title)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
