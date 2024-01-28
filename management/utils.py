from datetime import date, datetime, timedelta
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from .models import Reservation, Strike, Penalty, StrikeGroup, Notification


def calculate_penalty_price(
        end_date: datetime = None, initial_price: float = None,
        returned_date: datetime = None) -> float:

    if end_date and returned_date and initial_price:
        try:
            if end_date >= returned_date:
                return 0.0
            else:
                base_penalty_per_day = 4.0
                delay = (returned_date - end_date).days
                penalty_price = delay * base_penalty_per_day

                return round(penalty_price, 2)
        except:
            pass

    return None


def create_notification(user=None, title=None, message=None, obj=None):

    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        content_object=obj
    )

    return notification


def create_strike(res: None, reason: None):

    strike = Strike.objects.create(
        reservation=res,
        reason=reason
    )

    return strike


def create_penalty(user):
    penalties = Penalty.objects.filter(user=user)
    pen_counts = 0
    pen_days = 0

    if penalties.exists():
        pen_counts = penalties.count()

        if pen_counts == 1:
            pen_days = 60
            end_date_prev = date.today() + timedelta(days=pen_days)
        elif pen_counts == 2:
            pen_days = None
            end_date_prev = None
        # else:
        #     raise ValidationError('Impossible to create penalization')
    else:
        pen_days = 30
        end_date_prev = date.today() + timedelta(days=30)

    penalty = Penalty.objects.create(
        user=user,
        start_date=date.today(),
        end_date=end_date_prev
    )

    create_notification(
        user,
        title=f"You have been penalized.",
        message=f"Hi {user},",
        obj=penalty
    )

    return penalty


def add_strike_to_strike_group(user, strike: Strike):
    try:
        strike_group = StrikeGroup.objects.get(user=user, penalty=None)

        strike_group.strikes.add(strike)

        if strike_group.strikes.count() == 3:
            penalty = create_penalty(user)
            strike_group.penalty = penalty
            strike_group.save()

    except ObjectDoesNotExist:
        strike_group = StrikeGroup.objects.create(user=user)
        strike_group.strikes.add(strike)

    return strike_group
