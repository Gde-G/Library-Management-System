from django.db import models
from django.utils.translation import gettext_lazy as _


class DatesRecordsBaseModel(models.Model):
    create_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date of creation'))
    modify_at = models.DateTimeField(auto_now=True, verbose_name=_('Date of last modification'))

    class Meta:
        abstract = True
