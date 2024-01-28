from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


from core.models import DatesRecordsBaseModel


def get_profile_file_upload_path(self, filename):
    return f'users/{self.username}/{filename}'


class CustomAccountManager(BaseUserManager):

    def create_user(self, first_name, last_name, username, email, password, **other_fields):
        if not email:
            raise ValueError(_("You must provide a email address!"))

        if not username:
            raise ValueError(_("You must provide a username!"))

        if not first_name:
            raise ValueError(_("You must provide a first_name!"))

        if not last_name:
            raise ValueError(_("You must provide a last_name!"))

        if not password:
            raise ValueError(_("You must provide a password!"))

        email = self.normalize_email(email)

        user = self.model(email=email, first_name=first_name,
                          last_name=last_name, username=username,
                          **other_fields)

        validate_password(password)
        user.set_password(password)
        user.save()

        return user

    def create_superuser(self, first_name, last_name, username, email, password, **other_fields):
        other_fields.setdefault('is_staff', True)
        other_fields.setdefault('is_superuser', True)
        other_fields.setdefault('is_active', True)

        if other_fields.get('is_staff') is not True:
            raise ValueError('Restricted Access')
        if other_fields.get('is_superuser') is not True:
            raise ValueError('Restricted Access')

        return self.create_user(first_name, last_name, username, email, password, **other_fields)


class User(AbstractBaseUser, PermissionsMixin, DatesRecordsBaseModel):

    first_name = models.CharField(_('First Name'), max_length=100)
    last_name = models.CharField(_('Last Name'), max_length=100)
    username = models.CharField(max_length=100, unique=True)

    profile_img = models.ImageField(
        upload_to=get_profile_file_upload_path, null=True, blank=True)
    email = models.EmailField(unique=True)

    birth_date = models.DateField(null=True, blank=True)

    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    objects = CustomAccountManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __str__(self):
        return self.username


class ResetLink(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255)
    expiration_time = models.DateTimeField()
    used = models.BooleanField(default=False)

    def is_valid(self):
        """
        Check if the reset link is valid (not used and not expired).
        """
        now = timezone.now()
        return not self.used and self.expiration_time > now

    def mark_as_used(self):
        """
        Mark the reset link as used.
        """
        self.used = True
        self.save()
