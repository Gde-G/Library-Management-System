import random

from .models import User


def generate_available_username_suggestions(base_user_handle, max_suggestions=3):
    existing_user_handles = User.objects.all().values('user_handle')

    suggestions = []
    for i in range(1, max_suggestions + 1):
        suggestion = f"{base_user_handle}{random.randint(10, 1000)}"
        if suggestion not in existing_user_handles:
            suggestions.append(suggestion)
    return suggestions
