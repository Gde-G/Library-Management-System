# Generated by Django 4.2.9 on 2024-01-27 20:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='book',
            name='is_available',
        ),
    ]
