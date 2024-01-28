# Generated by Django 4.2.9 on 2024-01-24 17:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0012_alter_notification_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservation',
            name='status',
            field=models.CharField(choices=[('canceled_user', 'Canceled by the user'), ('canceled_system', 'Canceled by the system'), ('confirmed', 'Confirmed'), ('available', 'Available for Pickup'), ('retired', 'Retired'), ('expired', 'End Time Expired - Must be Returned'), ('waiting_payment', 'Waiting payment'), ('completed', 'Completed')], default='confirmed', max_length=20),
        ),
    ]
