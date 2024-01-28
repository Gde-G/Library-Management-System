from datetime import date

from celery import shared_task
from celery.utils.log import get_logger

from django.db.models import Q

from .models import Reservation, Notification, Penalty, Credit
from .utils import (
    calculate_penalty_price, create_notification,
    create_strike, add_strike_to_strike_group
)


@shared_task
def notifications_as_read(user, notifications):
    try:

        notis = Notification.objects.filter(
            Q(id__in=notifications)
        )
        if notis.exists():
            for noti in notis:

                noti.is_read = True
                noti.save()

            return f'Task completed successfully.'
        return f'No noti. Task completed successfully.'
    except Exception as e:
        return f"Task Fail : {str(e)}"


@shared_task
def reservation_retired_to_expire():
    some_fail = False
    errors = []
    today = date.today()
    try:
        res = Reservation.objects.filter(
            Q(end_date__lt=today) &
            Q(status__iexact='retired')
        )
    except Exception as query_error:
        return f"Query failed: {str(query_error)}"

    for r in res:
        try:
            r.status = 'expired'
            r.save()

            r.refresh_from_db()

            strike = create_strike(
                res=r,
                reason=f'You must return the Book, {r.book} on {r.end_date}'
            )

            create_notification(
                user=r.user,
                title="Strike issued for not returning the book on time",
                message=f"Dear {r.user}, a strike has been issued against your account due to the late return of the book {r.book}. "
                        f"Remember that you reserved the book from {r.start_date} to {r.end_date}, "
                        f"we remind you that for each day past the deadline you will be charged an extra $4.",
                obj=strike
            )

            add_strike_to_strike_group(user=r.user, strike=strike)

            res_to_cancel = Reservation.objects.filter(
                book=r.book, start_date=today).first()

            if res_to_cancel:
                apply_credits.delay(reservation=res_to_cancel)

        except Exception as e:
            some_fail = True
            errors.append({'reservation_id': r.id, 'error': e})

    if some_fail:
        return {'message': 'Task finish with errors.', 'errors': errors}
    else:
        return 'Task completed successfully.'


@shared_task
def apply_credits(reservation):
    msg_note = f" The reservation was canceled by the system because other user" \
        f" don't return the book, {reservation.book}, on time. We are going to compensate to" \
        f" {reservation.user} give credits that can use for future reservation."

    reservation.status = 'canceled_system'

    if reservation.notes:
        reservation.notes += msg_note
    else:
        reservation.notes = msg_note

    credits, create = Credit.objects.get_or_create(user=reservation.user)

    credits.amount += 4
    credits.save()

    noti_msg = f" Due to another user not returning their reserved book,{reservation.book} on time," \
        f" you've been compensated with 4 credits. You can use these credits to reserve another book." \
        f" Thank you for your understanding!"
    create_notification(
        user=reservation.user,
        title='You receive Credits like compensation for Missed Reservation',
        message=noti_msg,
        obj=credits,
    )

    return 'Task Complete successfully.'


@shared_task
def reservation_confirm_to_available():
    some_fail = False
    errors = []
    try:
        reservations = Reservation.objects.filter(
            Q(start_date__lte=date.today()) &
            Q(status__exact='confirmed')
        )
    except Exception as query_error:
        return f"Query failed: {str(query_error)}"

    for res in reservations:
        try:
            res.status = 'available'
            res.save()

            create_notification(
                user=res.user,
                title="Book Available to be retire.",
                message=f"Good news! Your reservation for the book {res.book} from {res.start_date} to {res.end_date} "
                        f"is now available for pickup.",
                obj=res
            )

        except Exception as e:
            some_fail = True
            errors.append({'reservation_id': res.id, 'error': e})

    if some_fail:
        return {'message': 'Task finish with errors.', 'errors': errors}
    else:
        return 'Task completed successfully.'


@shared_task
def reservation_end_and_never_pickup():
    some_fail = False
    errors = []
    try:
        res = Reservation.objects.filter(
            Q(end_date__lte=date.today()) &
            Q(status__iexact='available')
        )
    except Exception as query_error:
        return f"Query failed: {str(query_error)}"

    for r in res:
        try:
            r.status = 'waiting_payment'
            r.penalty_price = 0.0
            r.final_price = r.initial_price
            r.notes = f"The reservation of the book {r.book} made from {r.start_date} to " \
                f"{r.end_date} ended. Even though you never picked up the book, " \
                f"you must still pay the amount since you deprived another user " \
                f"of purchasing it for this period of time."

            r.save()

        except Exception as e:
            some_fail = True
            errors.append({'reservation_id': r.id, 'error': e})

    if some_fail:
        return {'message': 'Task finish with errors.', 'errors': errors}
    else:
        return 'Task completed successfully.'


@shared_task
def completed_penalization():
    some_fail = False
    errors = []

    try:
        penalties = Penalty.objects.filter(
            ~ Q(end_date=None) &
            (Q(end_date__lt=date.today()) &
             Q(complete__exact=False))
        )
    except Exception as query_error:
        return f"Query failed: {str(query_error)}"

    for pen in penalties:
        try:
            pen.complete = True
            pen.save()

            create_notification(
                user=pen.user,
                title="Penalization Ended.",
                message=f"Good news {pen.user}! The penalization period has ended. "
                        f"You are now free from any associated restrictions.",
                obj=pen
            )

        except Exception as e:
            some_fail = True
            errors.append({'penalty_id': pen.id, 'error': e})

    if some_fail:
        return {'message': 'Task finish with errors.', 'errors': errors}
    else:
        return 'Task completed successfully.'
