from __future__ import absolute_import, unicode_literals

from celery import Celery
from celery.schedules import crontab
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library.settings')

app = Celery('library')
app.conf.enable_utc = False

app.conf.update(timezone='America/Argentina/Cordoba')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Celery Beat settings
app.conf.beat_schedule = {
    'reservation_retired_to_expire': {
        'task': 'management.tasks.reservation_retired_to_expire',
        'schedule': crontab(hour=00, minute=00),
    },
    'reservation_confirm_to_available': {
        'task': 'management.tasks.reservation_confirm_to_available',
        'schedule': crontab(hour=00, minute=10),
    },
    'reservation_end_and_never_pickup': {
        'task': 'management.tasks.reservation_end_and_never_pickup',
        'schedule': crontab(hour=00, minute=20),
    },
    'reservation_end_and_never_pickup': {
        'task': 'management.tasks.completed_penalization',
        'schedule': crontab(hour=00, minute=30),
    },

}


app.autodiscover_tasks()
