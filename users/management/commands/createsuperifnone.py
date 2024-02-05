from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os


class Command(BaseCommand):
    help = 'Create a superuser if no users exist.'

    def handle(self, *args, **options):
        if not get_user_model().objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.SUCCESS('No users found. Creating a superuser...'))

            get_user_model().objects.create_superuser(
                username=os.environ.get('SUPERUSER_USERNAME'),
                email=os.environ.get('SUPERUSER_EMAIL'),
                password=os.environ.get('SUPERUSER_PASSWORD'),
                first_name=os.environ.get('SUPERUSER_FIRSTNAME'),
                last_name=os.environ.get('SUPERUSER_LASTNAME'),
                
                )

            self.stdout.write(self.style.SUCCESS('Superuser created successfully.'))
        else:
            self.stdout.write(self.style.SUCCESS('Users already exist.'))