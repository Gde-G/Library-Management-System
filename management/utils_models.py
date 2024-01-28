from datetime import datetime, date
from django.db.models import Q
# from .models import Notification, Reservation


def calculate_initial_price(start_date: datetime = None, end_date: datetime = None) -> float:
    if start_date and end_date:
        try:
            base_price_per_day = 2.0
            duration = (end_date - start_date).days + 1

            base_price = duration * base_price_per_day

            return round(base_price, 2)

        except:
            pass

    return None


# def create_notification_for_reservation_status(reservation):
#     if reservation.status == 'available':
#         title = f'Reservation of book: {reservation.book}, is now available to be retired.'
#         message = None
#     elif reservation.status == 'expired':
#         title = f'Book not returned on time: {reservation.book}, must be returned.'
#         message = f"When you made the reservation for the book '{reservation.book}' from {reservation.start_date.strftime('%d-%m-%Y')} to {reservation.end_date.strftime('%d-%m-%Y')}. The return deadline has passed, therefore, a penalty fee of $4 per day will be added to the price until the book is returned."

#         res_crash = Reservation.objects.filter(
#             Q(book=reservation.book) &
#             Q(start_date__lte=date.today()) &
#             Q(start_date__gte=reservation.end_date)
#         )
