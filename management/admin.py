from django.contrib import admin
from .models import Reservation, Credit, Strike, Penalty, StrikeGroup, Notification


admin.site.register(Reservation)
admin.site.register(Credit)
admin.site.register(Strike)
admin.site.register(Penalty)
admin.site.register(StrikeGroup)
admin.site.register(Notification)
