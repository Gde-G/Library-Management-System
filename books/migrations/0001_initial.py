# Generated by Django 5.0 on 2024-01-03 18:14

import books.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Genre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('slug', models.SlugField(blank=True, max_length=160, null=True, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Publisher',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
                ('country', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('nationality', models.CharField(blank=True, max_length=50, null=True)),
                ('birth_date', models.DateField()),
                ('death_date', models.DateField(blank=True, null=True)),
                ('biography', models.TextField()),
                ('picture', models.ImageField(upload_to=books.models.create_authors_pic_path)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Author',
                'verbose_name_plural': 'Authors',
                'unique_together': {('first_name', 'last_name')},
            },
        ),
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_at', models.DateTimeField(auto_now_add=True, verbose_name='Date of creation')),
                ('modify_at', models.DateTimeField(auto_now=True, verbose_name='Date of last modification')),
                ('title', models.CharField(max_length=200)),
                ('language', models.CharField(max_length=50)),
                ('edition', models.PositiveIntegerField(default=1)),
                ('amount_pages', models.PositiveIntegerField(default=1)),
                ('cover', models.ImageField(upload_to=books.models.create_books_cover_path)),
                ('publication_date', models.DateField()),
                ('slug', models.SlugField(blank=True, max_length=250, null=True, unique=True)),
                ('is_available', models.BooleanField(default=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='books.author')),
                ('genre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='books.genre', to_field='slug')),
                ('publisher', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='books.publisher')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
