from rest_framework.permissions import BasePermission
from .models import Penalty


class IsUserNotPenalized(BasePermission):
    message = "You are not allowed to reserve a book at this time, there is a penalty in effect."

    def has_permission(self, request, view):
        pen = Penalty.objects.filter(user=request.user, complete=False)
        if pen.exists():
            return False
        else:
            return True
