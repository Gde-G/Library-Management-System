from datetime import date

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from users.models import User
from books.models import Book

from .utils_models import calculate_initial_price


class Favorite(models.Model):
    user = models.ForeignKey(User, to_field='username',
                             on_delete=models.CASCADE)
    book = models.ForeignKey(Book, to_field='slug', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'book']


class Reservation(models.Model):
    STATUS_CHOICES = [
        ('canceled_user', 'Canceled by the user'),
        ('canceled_system', 'Canceled by the system'),
        ('confirmed', 'Confirmed'),
        ('available', 'Available for Pickup'),
        ('retired', 'Retired'),
        ('expired', 'End Time Expired - Must be Returned'),
        ('waiting_payment', 'Waiting payment'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(User, to_field='username',
                             on_delete=models.CASCADE)
    book = models.ForeignKey(Book, to_field='slug', on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    initial_price = models.DecimalField(
        max_digits=10, decimal_places=2)

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='confirmed')
    returned_date = models.DateField(null=True, blank=True)
    penalty_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    final_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)

    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.initial_price == None:
            self.initial_price = calculate_initial_price(
                self.start_date, self.end_date)

        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.username}, reserve the book {self.book} from {self.start_date} to {self.end_date}. Status, {self.status}'

class Credit(models.Model):
    user = models.OneToOneField(User, to_field='username',
                                on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.user}, {self.amount}.'


class Strike(models.Model):
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE)
    reason = models.TextField()

    def __str__(self):
        return f'{self.reservation.user} on reservation {self.reservation.id}.'


class Penalty(models.Model):
    user = models.ForeignKey(User, to_field='username',
                             on_delete=models.CASCADE)
    start_date = models.DateField(default=date.today)
    end_date = models.DateField(
        default=date.today, null=True, blank=True,
        help_text="Date on which the penalty will end. If is None/null, it means that the penalty is permanent."
    )

    complete = models.BooleanField(default=False)

    def __str__(self):
        if self.complete:
            return f"{self.user.username} penalization completed."
        else:
            if self.end_date:
                return f"{self.user.username} penalized until {self.end_date.strftime('%d-%m-%Y')}."
            else:
                return f"{self.user.username} penalized forever."


class StrikeGroup(models.Model):
    user = models.ForeignKey(User, to_field='username',
                             on_delete=models.CASCADE)
    penalty = models.OneToOneField(
        Penalty, on_delete=models.CASCADE, null=True, blank=True)
    strikes = models.ManyToManyField(Strike, blank=True)

    def clean(self):
        if self.strikes.count() > 3:
            raise ValidationError(
                'A StrikeGroup can only have a maximum of 3 strikes.')

    def __str__(self):
        return f'Strikes for Penalty: {self.penalty}'


class Notification(models.Model):
    user = models.ForeignKey(User, to_field='username',
                             on_delete=models.CASCADE)
    title = models.CharField(max_length=250)
    message = models.TextField(null=True, blank=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            'is_read',
            '-created_at',
        ]

    def __str__(self):
        return f"{self.user}, {self.title}"
