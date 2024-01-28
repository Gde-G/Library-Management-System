from datetime import date
from django.db.models import Q
from django.db import transaction
from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema, OpenApiParameter

from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated

from core.serializers import DetailSerializer, DummySerializer
from core.utils import GenericPagination

from .serializers import *
from .permissions import IsUserNotPenalized
from .tasks import notifications_as_read


class FavoriteViewSet(viewsets.GenericViewSet):
    serializer_class = DummySerializer
    permission_classes = [IsAuthenticated, ]
    pagination_class = GenericPagination
    lookup_field = 'book'

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateFavoriteSerializer
        elif self.action == 'list':
            return ListFavoriteSerializer

        return self.serializer_class

    def get_queryset(self, lookup=None):
        if lookup:
            return Favorite.objects.select_related('book').filter(user=self.request.user, book=lookup)
        else:
            return Favorite.objects.select_related('book').filter(user=self.request.user).order_by('-created_at')

    @extend_schema(
        responses={200: ListFavoriteSerializer},
        parameters=[
            OpenApiParameter(
                name='page', description='Page number.', type=int),
            OpenApiParameter(
                name='page_size', description='Amount of results per page (max 30).', type=int),
        ],
    )
    def list(self, request, *args, **kwargs):
        """
            List of user's favorite books (Only Users that are Authenticate). \n

            ### Query Parameters :\n

            - `page` (int): Page to get.\n
            - `page_size` (int): Amount of favorites books to get per page.\n

            ### Response(Success):\n
            - `200 OK` : List of Books objects.\n
                - `count` (int): Amount of TOTAL objects.\n
                - `next` (str): if exists, URL of the next objects, otherwise null.\n
                - `prev` (str):  if exists, URL of the previous objects, otherwise null.\n
                - `results` (list): List of Books\n
                    - `title` (str): Book Title.\n
                    - `language` (str): Language in which the book is written.\n
                    - `edition` (int): Number of edition.\n
                    - `amount_pages` (int): Number of pages the book has.\n
                    - `cover` (file): Binary forCover of the book.\n
                    - `publication_date` (str): Date when it was published in YYYY-mm-dd format.\n
                    - `slug` (str): Slug of the book, that we use as identifier.\n
                    - `genre` (object): Genre.\n
                        - `name` (str): Genre name.\n
                        - `description` (str): Genre Description.\n
                        - `slug` (str): Genre slug.\n
                    - `publisher` (object): Publisher, if not exists going to be null.\n
                        - `name` (str): Publisher name.\n
                        - `country` (str): Publisher Description.\n
                        - `id` (int): Publisher Identifier.\n
                    - `author` (object): Author, if not exists going to be null.\n
                        - `id` (int): Author Identifier.\n
                        - `name` (str): Author First name + Last name.\n
                        - `biography` (str): Author Biography.\n
                        - `picture` (str): Path where is store the Author picture .\n
                        - `nationality` (str): ISO 3166-1 (alpha-2 code) of the Nationality.\n
                        - `birth_date` (str): Date of birth in format YYYY-mm-dd.\n
                        - `death_date` (str)(null): Date of death in the YYYY-mm-dd format. Otherwise, if is alive just be null.\n\n

            ### Response(Failure):\n
            - `401 Unauthorized`:
            If the user is not authenticated.\n
            - `404 Not Found`: 
            Favorite/s not be found.\n
        """

        fav_books = self.get_queryset()
        if fav_books.exists():
            fav_books_serializer = self.get_serializer_class()(
                instance=[book.book for book in fav_books], many=True)
            paginator = self.pagination_class()
            paginated_data = paginator.paginate_queryset(
                fav_books_serializer.data,
                request,
                view=self
            )
            return paginator.get_paginated_response(paginated_data)

        else:
            return Response({'detail': 'Favorite books not found.'}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(responses={201: DetailSerializer})
    def create(self, request: Request, *args, **kwargs):
        """
            Create Favorite (Only Users that are Authenticate).\n

            ### Request Body :\n
            - `slug` (str): Slug of the book to make it favorite.\n

            ### Response(Success):\n
            - `201 Create` : Favorite create.\n
                - `detail` (str): Book add to favorite successfully..\n\n

            ### Response(Failure):\n
            - `400 BAD REQUEST`: 
            Invalid input data. Check the response for details.\n
            - `401 Unauthorized`:
            If the user is not authenticated.\n
        """
        fav_serializer = self.get_serializer_class()(data=request.data)
        if fav_serializer.is_valid():
            if not fav_serializer.Meta.model.objects.filter(book=fav_serializer.validated_data['book'], user=request.user).exists():
                fav_serializer.Meta.model.objects.create(
                    book=fav_serializer.validated_data['book'],
                    user=request.user
                )

                return Response({'detail': 'Book add to favorite successfully.'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'fav': 'This book already be mark as favorite by the authenticate user.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(fav_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={204: DummySerializer})
    def destroy(self, request, book=None, *args, **kwargs):
        """
            Delete Favorite (Only Users that are Authenticate).\n

            ### Path Parameter:\n
            - `slug` (str): Slug of the book to remove from favorites.\n

            ### Response(Success):\n
            - `204 NO CONTENT` : Favorite deleted.\n


            ### Response(Failure):\n
            - `400 BAD REQUEST`: 
            Invalid input data. Check the response for details.\n
            - `401 Unauthorized`:
            If the user is not authenticated.\n
            - `404 Not found`:
            Book not is in the favorite of this user.\n
        """
        if book:
            fav = self.get_queryset(lookup=book)

            if fav.exists():
                fav.delete()

                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({'detail': 'Fav on this book not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'detail': 'Book slug invalid.'}, status=status.HTTP_400_BAD_REQUEST)


class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = CreateReservationSerializer
    pagination_class = GenericPagination

    def get_queryset(self, lookup=None, book=None, start_date=None, end_date=None):
        if lookup:
            return Reservation.objects.select_related('book').filter(user=self.request.user, id=lookup).first()

        if book and start_date and end_date:
            overlapping_reservations = Reservation.objects.select_related('book').filter(
                Q(book__slug__exact=book) &
                Q(start_date__lte=end_date) &
                Q(end_date__gte=start_date) &
                Q(status__in=['confirmed', 'available', 'expired', 'retired'])
            )
            return overlapping_reservations
        if book:
            today = date.today()
            unavailable_periods = Reservation.objects.select_related('book').filter(
                Q(book__slug__exact=book) &
                Q(end_date__gte=today) &
                Q(status__in=['confirmed', 'available', 'expired', 'retired'])
            ).values('start_date', 'end_date').order_by('-start_date')

            return unavailable_periods

        return Reservation.objects.select_related('book').filter(user=self.request.user).order_by('start_date')

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateReservationSerializer
        elif self.action in ['list', 'retrieve']:
            return ListReservationSerializer
        elif self.action == 'partial_update':
            return PatchReservationSerializer
        elif self.action in ['update', 'destroy']:
            return DummySerializer
        elif self.action == 'check_availability_to_reservation':
            return CheckReservationAvailabilitySerializer
        elif self.action == 'unavailable_periods_to_reservation':
            return UnavailableReservationPeriodsSerializer

    def get_permissions(self):

        if self.action in ['check_availability_to_reservation', 'unavailable_periods_to_reservation']:
            return [AllowAny(), ]
        elif self.action == 'create':
            return [IsAuthenticated(), IsUserNotPenalized()]
        elif self.action in ['list', 'retrieve', 'destroy']:
            return [IsAuthenticated(), ]
        else:
            return [IsAdminUser(), ]

    @extend_schema(responses={201: DetailSerializer})
    def create(self, request, *args, **kwargs):
        '''
            Create Reservation of a book  (Only Users that are Authenticate).\n

            ### Request Body :\n
            - `book` (str): Slug of the book to make the reservation.\n
            - `start_date` (str): Date, format YYYY-mm-dd, that is going to start the reservation.\n
            - `end_date` (str): Date, format YYYY-mm-dd, that is going to end the reservation.\n
            - `notes` (str): Some note or helpful text to add the reservation.\n
            ### Response(Success):\n
            - `201 Create` : Reservation created.\n
                - `detail` (str): Book reservation was made successfully..\n\n

            ### Response(Failure):\n
            - `400 BAD REQUEST`: 
            Invalid input data. Check the response for details.\n
            - `401 Unauthorized`:
            If the user is not authenticated.\n
            - `403 For bidden`:
            The user has a penalty in progress..\n
        '''
        penalty = Penalty.objects.filter(
            user=self.request.user,
            complete=False
        )
        if not penalty:

            reservation_serializer = self.get_serializer_class()(data=request.data)
            if reservation_serializer.is_valid():
                reservation_serializer.save(user=request.user)
                return Response({'detail': 'Reservation was made successfully.'}, status=status.HTTP_201_CREATED)
            else:
                return Response(reservation_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {'detail': f'You can not reserve a book until {penalty.end_date.strftime("%d-%m-%Y")}.'},
                status=status.HTTP_403_FORBIDDEN
            )

    @extend_schema(
        responses={200: ListReservationSerializer},
        parameters=[
            OpenApiParameter(
                name='page', description='Page number.', type=int),
            OpenApiParameter(
                name='page_size', description='Amount of results per page (max 30).', type=int),
        ],
    )
    def list(self, request, *args, **kwargs):
        """
            List of user's reservations of books (Only Users that are Authenticate). \n

            ### Query Parameters :\n

            - `page` (int): Page to get.\n
            - `page_size` (int): Amount of reservations to get per page.\n

            ### Response(Success):\n
            - `200 OK` : List of reservations objects.\n
                - `count` (int): Amount of TOTAL objects.\n
                - `next` (str): if exists, URL of the next objects, otherwise null.\n
                - `prev` (str):  if exists, URL of the previous objects, otherwise null.\n
                - `results` (list): List of Reservations\n
                    - `id` (int): Reservation ID.\n
                    - `start_date` (str): Date, format YYYY-mm-dd, that is going to start the reservation.\n
                    - `end_date` (str): Date, format YYYY-mm-dd, that is going to end the reservation.\n
                    - `initial_price` (decimal): Price for the period of reservation.\n
                    - `status` (str): Status of the book reservation.\n
                        - canceled_user, canceled_system, confirmed, available, retired, expired, waiting_payment, completed.
                    - `returned_date` (str): Date, format YYYY-mm-dd, when the reserved book was returned, if it has not been returned yet, it will return null.\n
                    - `penalty_price` (decimal): Penalty price. If book not was returned on the period that was reservation, otherwise be 0.0.\n
                    - `final_price` (decimal): Price for the period of reservation, null if not end or not was returned.\n
                    - `notes` (str): Some note or helpful text to add the reservation.\n
                    - `created_at` (str): Date time, format YYYY-mm-ddTHH:MM:SS.Z, when was created the reservation.\n
                    - `book` (object): Book.\n 
                        - `title` (str): Book Title.\n
                        - `language` (str): Language in which the book is written.\n
                        - `edition` (int): Number of edition.\n
                        - `amount_pages` (int): Number of pages the book has.\n
                        - `cover` (file): Binary forCover of the book.\n
                        - `publication_date` (str): Date when it was published in YYYY-mm-dd format.\n
                        - `slug` (str): Slug of the book, that we use as identifier.\n
                        - `genre` (object): Genre.\n
                            - `name` (str): Genre name.\n
                            - `description` (str): Genre Description.\n
                            - `slug` (str): Genre slug.\n
                        - `publisher` (object): Publisher, if not exists going to be null.\n
                            - `name` (str): Publisher name.\n
                            - `country` (str): Publisher Description.\n
                            - `id` (int): Publisher Identifier.\n
                        - `author` (object): Author, if not exists going to be null.\n
                            - `id` (int): Author Identifier.\n
                            - `name` (str): Author First name + Last name.\n
                            - `biography` (str): Author Biography.\n
                            - `picture` (str): Path where is store the Author picture .\n
                            - `nationality` (str): ISO 3166-1 (alpha-2 code) of the Nationality.\n
                            - `birth_date` (str): Date of birth in format YYYY-mm-dd.\n
                            - `death_date` (str)(null): Date of death in the YYYY-mm-dd format. Otherwise, if is alive just be null.\n\n

            ### Response(Failure):\n
            - `401 Unauthorized`:
            If the user is not authenticated.\n
            - `404 Not Found`: 
            Reservation/s not be found.\n
        """

        reservations = self.get_queryset()
        if reservations.exists():

            reservation_serializer = self.get_serializer_class()(
                instance=reservations, many=True)
            paginator = self.pagination_class()
            paginated_data = paginator.paginate_queryset(
                reservation_serializer.data,
                request,
                view=self
            )
            return paginator.get_paginated_response(paginated_data)
        else:
            return Response({'detail': 'Reservation not found.'}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        responses={200: ListReservationSerializer}
    )
    def retrieve(self, request, pk=None, *args, **kwargs):
        """
            Retrieve reservations of books (Only Users that are Authenticate). \n

            ### Path Parameter:\n
            - `id` (int): Reservation ID of the reservation that want to get.\n

            ### Response(Success):\n
            - `200 OK` : List of reservations objects.\n
                - `id` (int): Reservation ID.\n
                - `start_date` (str): Date, format YYYY-mm-dd, that is going to start the reservation.\n
                - `end_date` (str): Date, format YYYY-mm-dd, that is going to end the reservation.\n
                - `initial_price` (decimal): Price for the period of reservation.\n
                - `status` (str): Status of the book reservation.\n
                    - canceled_user, canceled_system, confirmed, available, retired, expired, waiting_payment, completed.
                - `returned_date` (str): Date, format YYYY-mm-dd, when the reserved book was returned, if it has not been returned yet, it will return null.\n
                - `penalty_price` (decimal): Penalty price. If book not was returned on the period that was reservation, otherwise be 0.0.\n
                - `final_price` (decimal): Price for the period of reservation, null if not end or not was returned.\n
                - `notes` (str): Some note or helpful text to add the reservation.\n
                - `created_at` (str): Date time, format YYYY-mm-ddTHH:MM:SS.Z, when was created the reservation.\n
                - `book` (object): Book.\n 
                    - `title` (str): Book Title.\n
                    - `language` (str): Language in which the book is written.\n
                    - `edition` (int): Number of edition.\n
                    - `amount_pages` (int): Number of pages the book has.\n
                    - `cover` (file): Binary forCover of the book.\n
                    - `publication_date` (str): Date when it was published in YYYY-mm-dd format.\n
                    - `slug` (str): Slug of the book, that we use as identifier.\n
                    - `genre` (object): Genre.\n
                        - `name` (str): Genre name.\n
                        - `description` (str): Genre Description.\n
                        - `slug` (str): Genre slug.\n
                    - `publisher` (object): Publisher, if not exists going to be null.\n
                        - `name` (str): Publisher name.\n
                        - `country` (str): Publisher Description.\n
                        - `id` (int): Publisher Identifier.\n
                    - `author` (object): Author, if not exists going to be null.\n
                        - `id` (int): Author Identifier.\n
                        - `name` (str): Author First name + Last name.\n
                        - `biography` (str): Author Biography.\n
                        - `picture` (str): Path where is store the Author picture .\n
                        - `nationality` (str): ISO 3166-1 (alpha-2 code) of the Nationality.\n
                        - `birth_date` (str): Date of birth in format YYYY-mm-dd.\n
                        - `death_date` (str)(null): Date of death in the YYYY-mm-dd format. Otherwise, if is alive just be null.\n\n

            ### Response(Failure):\n
            - `400 BAS REQUEST`:
            Invalid id for a reservation.\n
            - `401 Unauthorized`:
            If the user is not authenticated.\n
            - `404 Not Found`: 
            Reservation not be found.\n
        """

        if pk and pk.isdigit():
            reservation = self.get_queryset(lookup=pk)
            if reservation:
                reservation_serializer = self.get_serializer_class()(reservation)
                return Response(reservation_serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'Reservation not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'detail': 'Invalid pk.'}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(request=DummySerializer, responses={405: DetailSerializer})
    def update(self, request, *args, **kwargs):
        '''### Method not allowed, use PATCH.'''
        return Response({'detail': 'Method not allowed.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @extend_schema(responses={202: ListReservationSerializer})
    def partial_update(self, request, pk=None, *args, **kwargs):
        '''
            Update Reservation (Only Users with Admin Range).\n

            ### Path Parameter:\n
            - `id` (int): Reservation ID of the reservation that want to update.\n

            ### Request Body :\n
            Must have one of the two options.
            - `retired` (bool)(optional): Mark as retired when the use pick up the book that corresponds with the reservation.\n
            - `returned_date` (str)(optional): Date, format YYYY-mm-dd, when be returned the book that corresponds to the reservation.\n


            ### Response(Success):\n
            - `200 OK` : List of reservations objects.\n
                - `detail` (str): Updated successfully.\n
                - `result` (object): Reservation\n
                    - `id` (int): Reservation ID.\n
                    - `start_date` (str): Date, format YYYY-mm-dd, that is going to start the reservation.\n
                    - `end_date` (str): Date, format YYYY-mm-dd, that is going to end the reservation.\n
                    - `initial_price` (decimal): Price for the period of reservation.\n
                    - `status` (str): Status of the book reservation.\n
                        - canceled_user, canceled_system, confirmed, available, retired, expired, waiting_payment, completed.
                    - `returned_date` (str): Date, format YYYY-mm-dd, when the reserved book was returned, if it has not been returned yet, it will return null.\n
                    - `penalty_price` (decimal): Penalty price. If book not was returned on the period that was reservation, otherwise be 0.0.\n
                    - `final_price` (decimal): Price for the period of reservation, null if not end or not was returned.\n
                    - `notes` (str): Some note or helpful text to add the reservation.\n
                    - `created_at` (str): Date time, format YYYY-mm-ddTHH:MM:SS.Z, when was created the reservation.\n
                    - `book` (object): Book.\n 
                        - `title` (str): Book Title.\n
                        - `language` (str): Language in which the book is written.\n
                        - `edition` (int): Number of edition.\n
                        - `amount_pages` (int): Number of pages the book has.\n
                        - `cover` (file): Binary forCover of the book.\n
                        - `publication_date` (str): Date when it was published in YYYY-mm-dd format.\n
                        - `slug` (str): Slug of the book, that we use as identifier.\n
                        - `genre` (object): Genre.\n
                            - `name` (str): Genre name.\n
                            - `description` (str): Genre Description.\n
                            - `slug` (str): Genre slug.\n
                        - `publisher` (object): Publisher, if not exists going to be null.\n
                            - `name` (str): Publisher name.\n
                            - `country` (str): Publisher Description.\n
                            - `id` (int): Publisher Identifier.\n
                        - `author` (object): Author, if not exists going to be null.\n
                            - `id` (int): Author Identifier.\n
                            - `name` (str): Author First name + Last name.\n
                            - `biography` (str): Author Biography.\n
                            - `picture` (str): Path where is store the Author picture .\n
                            - `nationality` (str): ISO 3166-1 (alpha-2 code) of the Nationality.\n
                            - `birth_date` (str): Date of birth in format YYYY-mm-dd.\n
                            - `death_date` (str)(null): Date of death in the YYYY-mm-dd format. Otherwise, if is alive just be null.\n\n

            ### Response(Failure):\n
            - `400 BAD REQUEST`: 
            Invalid input data. Check the response for details.\n
            - `401 Unauthorized`:
            If the user is not authenticated.\n
            - `404 Not Found`: 
            Reservation/s not be found.\n
        '''

        if pk and pk.isdigit():
            reservation = self.get_queryset(lookup=pk)
            if reservation:
                reservation_serializer = self.get_serializer_class()(
                    instance=reservation, data=request.data, partial=True
                )
                if reservation_serializer.is_valid():
                    reservation_serializer.save()
                    response_serializer_ret = ListReservationSerializer(
                        reservation, context={'request': request}
                    )
                    return Response(
                        {
                            'detail': 'Reservation modify successfully.',
                            'result': response_serializer_ret.data
                        },
                        status=status.HTTP_202_ACCEPTED
                    )

                else:
                    return Response(reservation_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'detail': 'Reservation Not Found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'detail': 'Invalid pk.'}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={204: DummySerializer})
    def destroy(self, request, pk=None, *args, **kwargs):
        """
            "Delete" Reservation (Only Users that are Authenticate).\n
            Change status to "canceled_user" ...

            ### Path Parameter:\n
            - `id` (int): Reservation ID of the reservation that want to as canceled.\n

            ### Response(Success):\n
            - `204 NO CONTENT` : Reservation canceled.\n

            ### Response(Failure):\n
            - `400 BAD REQUEST`: 
            Invalid input data. Check the response for details.\n
            - `401 Unauthorized`:
            If the user is not authenticated.\n
            - `403 For bidden`:
            Cannot cancel a reservation that has already started.\n
            - `404 Not found`:
            Book not is in the favorite of this user.\n
            - `500 Internal Server Error`:
            Something fail changing the status.\n
        """
        if pk and pk.isdigit():
            reservation = self.get_queryset(lookup=pk)
            if reservation:

                try:
                    if reservation.start_date > date.today():
                        reservation.status = 'canceled_user'
                        reservation.save()

                        return Response(status=status.HTTP_204_NO_CONTENT)
                    else:
                        return Response({'detail': 'Cannot cancel a reservation that has already started.'}, status=status.HTTP_403_FORBIDDEN)
                except:
                    return Response({'detail': 'Internal error, try later again.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            else:
                return Response({'detail': 'Reservation Not Found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'detail': 'Invalid pk.'}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=CheckReservationAvailabilitySerializer,
        responses={200: DetailSerializer},
        parameters=[
            OpenApiParameter(
                name='book', description='Slug of the book.', type=str, required=True),
            OpenApiParameter(
                name='start_date', description='Date, format YYYY-mm-dd, that is going to start the reservation.', type=str, required=True),
            OpenApiParameter(
                name='end_date', description='Date, format YYYY-mm-dd, that is going to end the reservation.', type=str, required=True),
        ],
    )
    @action(
        detail=False, methods=['GET'],
        url_path='check/availability',
        url_name='check-availability'
    )
    def check_availability_to_reservation(self, request, *args, **kwargs):
        '''
            Check Availability of a book in a specific period of time (ANY) \n
            ### Path Parameter:\n
            - `book` (str): Slug of the book.\n
            - `start_date` (str): Date, format YYYY-mm-dd, that is going to start the period.\n
            - `end_date` (str): Date, format YYYY-mm-dd, that is going to end the period.\n

            ### Response(Success):\n
            - `200 OK` : .\n
                - `is_available` (bool): Boolean value representing if is going to be available or not.\n

            ### Response(Failure):\n
            - `400 BAD REQUEST`:
            Invalid input data. Check the response for details\n
        '''
        availability_serializer = self.get_serializer_class()(data=request.query_params)
        if availability_serializer.is_valid():

            overlap = self.get_queryset(
                book=availability_serializer.validated_data['book'],
                start_date=availability_serializer.validated_data['start_date'],
                end_date=availability_serializer.validated_data['end_date'],
            )

            return Response({'is_available': not overlap.exists()}, status=status.HTTP_200_OK)
        else:
            return Response(availability_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={200: UnavailableReservationPeriodsSerializer},
        parameters=[
            OpenApiParameter(
                name='book', description='Slug of the book.', type=str, required=True),
        ],
    )
    @action(
        detail=False,
        methods=['GET'],
        url_path='unavailable/periods',
        url_name='unavailable-periods'
    )
    def unavailable_periods_to_reservation(self, request, *args, **kwargs):
        '''
            List Unavailability periods to reserve of a book (ANY). \n
            ### Path Parameter:\n
            - `book` (str): Slug of the book.\n

            ### Response(Success):\n
            - `200 OK` : List of periods.\n
                - `start_date` (string): Date, format YYYY-mm-dd, when start a reservation.\n
                - `end_date` (string): Date, format YYYY-mm-dd, when end a reservation.\n
            ### Response(Failure):\n
            - `400 Bad REQUEST`:
            Invalid input data. Check the response for details\n
            - `404 Not found`:
            Book with that slug not found.\n
        '''
        book = request.query_params.get('book', None)
        if book:
            book_q = Book.objects.filter(slug__iexact=book).first()
            if book_q:
                periods = self.get_queryset(book=book_q.slug)
                if periods.exists():
                    periods_serializer = self.get_serializer_class()(instance=periods, many=True)
                    return Response(periods_serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response([], status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'Bool parsed not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'book': 'Book slug required as query parameter.'}, status=status.HTTP_400_BAD_REQUEST)


class CreditViewSet(viewsets.GenericViewSet):
    serializer_class = CreditRetrieveSerializer

    def get_queryset(self):
        user_credit, create = Credit.objects.get_or_create(
            user=self.request.user
        )
        return user_credit

    def get_serializer_class(self):
        if self.action == 'subtract':
            return CreditPatchSerializer
        return self.serializer_class

    def get_permissions(self):
        if self.action == 'list':
            return [IsAuthenticated(), ]

        else:
            return [IsAdminUser(), ]

    @extend_schema(
        responses={200: serializer_class},
    )
    def list(self, request, *args, **kwargs):
        """
            List the credits that have a user (Only Users that are Authenticate). \n

            ### Response(Success):\n
            - `200 OK` : Credits.\n
                - `user` (str): Username of the user that is authenticate.\n
                - `amount` (int): Number of credits that have that user.\n

            ### Response(Failure):\n
            - `401 Unauthorized`:
            If the user is not authenticated.\n
            - `500 Internal Server Error`: 
            Detail of what fail.\n
        """
        try:
            credit = self.get_queryset()
            credit_serializer = self.get_serializer_class()(credit)

            return Response(credit_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': f'{e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        request=CreditPatchSerializer,
        responses={202: serializer_class},
    )
    @action(methods=['PATCH'], detail=False, url_name='subtract')
    def subtract(self, request, *args, **kwargs):
        '''
            Subtract credits (Only Users that are Authenticate). \n\n
            ### Request Body :\n
            - `subtract` (int): Positive integer to subtract from the amount of credits.\n\n

            ### Response(Success):\n
            - `202 ACCEPTED` : Credits.\n
                - `detail` (str): Successfully subtract of credits..\n
                - `credits` (object): Credits.\n 
                    - `user` (str): Username of the user that is authenticate.\n
                    - `amount` (int): Number of credits that have that user.\n\n
            ### Response(Failure):\n
            - `400 BAD REQUEST`: 
            Invalid input data. Check the response for details.\n
            - `401 Unauthorized`:
            If the user is not authenticated.\n
        '''

        credit = self.get_queryset()
        credit_serializer = self.get_serializer_class()(
            instance=credit, data=request.data, partial=True)

        if credit_serializer.is_valid():
            credit_serializer.save()
            credit.refresh_from_db()
            credit_serializer_ret = self.serializer_class(
                credit, context={'request': request}
            )
            return Response(
                {
                    'detail': 'Successfully subtract of credits.',
                    'credits': credit_serializer_ret.data
                },
                status=status.HTTP_202_ACCEPTED
            )

        else:
            return Response(credit_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StrikeViewSet(viewsets.GenericViewSet):
    serializer_class = StrikeListSerializer
    permission_classes = [IsAuthenticated,]

    def get_queryset(self):
        strikes = Strike.objects.filter(reservation__user=self.request.user)

        return strikes

    @extend_schema(responses={200: serializer_class})
    def list(self, request, *args, **kwargs):
        """
            List Strikes that received the authenticate user (Only Users that are Authenticate). \n

            ### Response(Success):\n
            - `200 OK` : List of Strikes.\n
                - `reason` (str): Explanation why received the strike.\n
                - `reservation` (object): Reservation object.\n
                    - `id` (int): Reservation ID.\n
                    - `start_date` (str): Date, format YYYY-mm-dd, that is going to start the reservation.\n
                    - `end_date` (str): Date, format YYYY-mm-dd, that is going to end the reservation.\n
                    - `initial_price` (decimal): Price for the period of reservation.\n
                    - `status` (str): Status of the book reservation.\n
                        - canceled_user, canceled_system, confirmed, available, retired, expired, waiting_payment, completed.
                    - `returned_date` (str): Date, format YYYY-mm-dd, when the reserved book was returned, if it has not been returned yet, it will return null.\n
                    - `penalty_price` (decimal): Penalty price. If book not was returned on the period that was reservation, otherwise be 0.0.\n
                    - `final_price` (decimal): Price for the period of reservation, null if not end or not was returned.\n
                    - `notes` (str): Some note or helpful text to add the reservation.\n
                    - `created_at` (str): Date time, format YYYY-mm-ddTHH:MM:SS.Z, when was created the reservation.\n
                    - `book` (object): Book.\n 
                        - `title` (str): Book Title.\n
                        - `language` (str): Language in which the book is written.\n
                        - `edition` (int): Number of edition.\n
                        - `amount_pages` (int): Number of pages the book has.\n
                        - `cover` (file): Binary forCover of the book.\n
                        - `publication_date` (str): Date when it was published in YYYY-mm-dd format.\n
                        - `slug` (str): Slug of the book, that we use as identifier.\n
                        - `genre` (object): Genre.\n
                            - `name` (str): Genre name.\n
                            - `description` (str): Genre Description.\n
                            - `slug` (str): Genre slug.\n
                        - `publisher` (object): Publisher, if not exists going to be null.\n
                            - `name` (str): Publisher name.\n
                            - `country` (str): Publisher Description.\n
                            - `id` (int): Publisher Identifier.\n
                        - `author` (object): Author, if not exists going to be null.\n
                            - `id` (int): Author Identifier.\n
                            - `name` (str): Author First name + Last name.\n
                            - `biography` (str): Author Biography.\n
                            - `picture` (str): Path where is store the Author picture .\n
                            - `nationality` (str): ISO 3166-1 (alpha-2 code) of the Nationality.\n
                            - `birth_date` (str): Date of birth in format YYYY-mm-dd.\n
                            - `death_date` (str)(null): Date of death in the YYYY-mm-dd format. Otherwise, if is alive just be null.\n\n

            ### Response(Failure):\n
            - `401 Unauthorized`:
            If the user is not authenticated.\n
            - `404 Not found`: 
            Authenticate user not receives Strikes.\n
        """

        strikes = self.get_queryset()
        if strikes.exists():
            strikes_serializer = self.serializer_class(
                instance=strikes, many=True)
            return Response(strikes_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'detail': "Strikes not found!"}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(responses={200: DetailSerializer})
    @action(methods=['GET'], detail=False, url_path="amount", url_name="amount")
    def get_amount(self, request, *args, **kwargs):
        '''
        Get amount of Strikes that received the authenticate user (Only Users that are Authenticate). \n

        ### Response(Success):\n
        - `200 OK` :\n
            - `amount_strikes` (int): Number of strikes the user has.\n

        ### Response(Failure):\n
        - `401 Unauthorized`:
            If the user is not authenticated.\n
        '''
        s_amount = self.get_queryset().count()
        return Response({'amount_strikes': s_amount}, status=status.HTTP_200_OK)


class PenaltyViewSet(viewsets.GenericViewSet):
    serializer_class = PenaltyListSerializer
    permission_classes = [IsAuthenticated, ]

    def get_queryset(self, lookup=None):
        if lookup:
            penalty = get_object_or_404(
                Penalty, id=lookup, user=self.request.user)
            strikes = StrikeGroup.objects.select_related(
                'penalty').filter(penalty=penalty).first()
            return strikes
        else:
            return Penalty.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PenaltyRetrieveSerializer

        else:
            return self.serializer_class

    @extend_schema(responses={200: serializer_class})
    def list(self, request, *args, **kwargs):
        """
            List the Penalties that have a user (Only Users that are Authenticate). \n

            ### Response(Success):\n
            - `200 OK` : List of Penalties.\n
                - `id` (int): Penalty ID.\n
                - `user` (str): Username of the user receives the Penalty (== authenticate user).\n
                - `start_date` (str): Date, format YYYY-mm-dd, that is going to start the Penalty.\n
                - `end_date` (str): Date, format YYYY-mm-dd, that is going to end the Penalty.\n
                - `complete` (boolean): If is complete(end_date < today)is True, otherwise is False.\n

            ### Response(Failure):\n
            - `401 Unauthorized`:
            If the user is not authenticated.\n
            - `404 Not found`: 
            Penalties not found.\n
        """

        penalties = self.get_queryset()
        if penalties.exists():
            penalties_serializer = self.get_serializer_class()(instance=penalties, many=True)
            return Response(penalties_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Penalties not found.'}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(responses={200: PenaltyRetrieveSerializer})
    def retrieve(self, request, pk=None, *args, **kwargs):
        """
            Retrieve Penalty that have a user (Only Users that are Authenticate). \n\n

            ### Path Parameter:\n
            - `id` (int): Penalty ID that want to get.\n\n

            ### Response(Success):\n
            - `200 OK` : \n
                - `penalty` (object): Penalty .\n
                    - `id` (int): Penalty ID.\n
                    - `user` (str): Username of the user receives the Penalty (== authenticate user).\n
                    - `start_date` (str): Date, format YYYY-mm-dd, that is going to start the Penalty.\n
                    - `end_date` (str): Date, format YYYY-mm-dd, that is going to end the Penalty.\n
                    - `complete` (boolean): If is complete(end_date < today)is True, otherwise is False.\n
                - `strikes` (objects): List of strikes.\n
                    - `reason` (str): Explanation why received the strike.\n
                    - `reservation` (object): Reservation object.\n
                        - `id` (int): Reservation ID.\n
                        - `start_date` (str): Date, format YYYY-mm-dd, that is going to start the reservation.\n
                        - `end_date` (str): Date, format YYYY-mm-dd, that is going to end the reservation.\n
                        - `initial_price` (decimal): Price for the period of reservation.\n
                        - `status` (str): Status of the book reservation.\n
                            - canceled_user, canceled_system, confirmed, available, retired, expired, waiting_payment, completed.
                        - `returned_date` (str): Date, format YYYY-mm-dd, when the reserved book was returned, if it has not been returned yet, it will return null.\n
                        - `penalty_price` (decimal): Penalty price. If book not was returned on the period that was reservation, otherwise be 0.0.\n
                        - `final_price` (decimal): Price for the period of reservation, null if not end or not was returned.\n
                        - `notes` (str): Some note or helpful text to add the reservation.\n
                        - `created_at` (str): Date time, format YYYY-mm-ddTHH:MM:SS.Z, when was created the reservation.\n
                        - `book` (object): Book.\n 
                            - `title` (str): Book Title.\n
                            - `language` (str): Language in which the book is written.\n
                            - `edition` (int): Number of edition.\n
                            - `amount_pages` (int): Number of pages the book has.\n
                            - `cover` (file): Binary forCover of the book.\n
                            - `publication_date` (str): Date when it was published in YYYY-mm-dd format.\n
                            - `slug` (str): Slug of the book, that we use as identifier.\n
                            - `genre` (object): Genre.\n
                                - `name` (str): Genre name.\n
                                - `description` (str): Genre Description.\n
                                - `slug` (str): Genre slug.\n
                            - `publisher` (object): Publisher, if not exists going to be null.\n
                                - `name` (str): Publisher name.\n
                                - `country` (str): Publisher Description.\n
                                - `id` (int): Publisher Identifier.\n
                            - `author` (object): Author, if not exists going to be null.\n
                                - `id` (int): Author Identifier.\n
                                - `name` (str): Author First name + Last name.\n
                                - `biography` (str): Author Biography.\n
                                - `picture` (str): Path where is store the Author picture .\n
                                - `nationality` (str): ISO 3166-1 (alpha-2 code) of the Nationality.\n
                                - `birth_date` (str): Date of birth in format YYYY-mm-dd.\n
                                - `death_date` (str)(null): Date of death in the YYYY-mm-dd format. Otherwise, if is alive just be null.\n\n

            ### Response(Failure):\n
            - `401 Unauthorized`:
            If the user is not authenticated.\n
            - `404 Not found`: 
            Penalties not found.\n
        """
        pen_strikes = self.get_queryset(lookup=pk)
        pen_strikes_serializers = self.get_serializer_class()(instance=pen_strikes)

        return Response(pen_strikes_serializers.data, status=status.HTTP_200_OK)

    @extend_schema(responses={200: DetailSerializer})
    @action(methods=['GET'], detail=False, url_path="amount", url_name="amount")
    def get_amount(self, request, *args, **kwargs):
        '''
        Get amount of Penalties that received the authenticate user (Only Users that are Authenticate). \n

        ### Response(Success):\n
        - `200 OK` : .\n
            - `amount_penalties` (int): Number of Penalties the user has.\n

        ### Response(Failure):\n
        - `401 Unauthorized`:
            If the user is not authenticated.\n
        '''
        p_amount = self.get_queryset().count()
        return Response({'amount_penalties': p_amount}, status=status.HTTP_200_OK)


class NotificationViewSet(viewsets.GenericViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated, ]
    pagination_class = GenericPagination

    def get_queryset(self, not_read=None, lookup=None):
        notis = None

        if not_read:
            notis = Notification.objects.filter(
                user=self.request.user,
                is_read=False
            )
        else:
            notis = Notification.objects.filter(
                user=self.request.user
            )
        if lookup:
            notis = Notification.objects.filter(
                id=lookup, user=self.request.user).first()

        return notis

    @extend_schema(
        responses={200: NotificationSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        """
            List notifications that have a user (Only Users that are Authenticate). \n

            ### Query Parameters:\n
            - `not_read` (boolean)(optional): If true, only fetch unread notifications.\n
            - `page` (int): Page to get.\n
            - `page_size` (int): Amount of notifications to get per page.\n\n

            ### Response (Success):\n
            - `200 OK`: List of notifications.\n
                - `id` (int): Notification ID.\n
                - `title` (str): Title of the notification.\n
                - `message` (str): Body of the notification.\n
                - `is_read` (boolean): Boolean that show if was read, True, or not False.\n
                - `created_at` (str): Date time when was sent.\n
                - `type` (str): Model name which is related the notification.\n
                - `variable(equal to the value of type)` (object): Entire object which is related the notification.\n
                    - `field_1` (int): Field of object.\n
                    - `field_2` (str): Another Field of object.\n
                    - `etcetera`\n\n

            ### Response (Failure):\n
            - `404 Not Found`:
            Notifications not found.\n
            - `500 Internal Server Error`:
            If an unexpected error occurs.\n
        """
        try:
            read = request.query_params.get('not_read', False)
            notis = self.get_queryset(not_read=read)

            if notis.exists():
                notis_serializer = self.serializer_class(
                    instance=notis, many=True)
                paginator = self.pagination_class()
                paginator_data = paginator.paginate_queryset(
                    notis_serializer.data,
                    request,
                    view=self
                )
                notis_ids = [noti['id'] for noti in paginator_data]

                notifications_as_read.delay(
                    user=request.user.username, notifications=notis_ids)

                return paginator.get_paginated_response(paginator_data)
            else:
                return Response({'detail': 'Notifications not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': f'Error on server side.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        responses={200: NotificationSerializer}
    )
    def retrieve(self, request, pk=None, *args, **kwargs):
        """
            Retrieve a specific notification (Only Users that are Authenticate). \n

            ### Response (Success):\n
            - `200 OK`: Notification.\n
                - `id` (int): Notification ID.\n
                - `title` (str): Title of the notification.\n
                - `message` (str): Body of the notification.\n
                - `is_read` (boolean): Boolean that show if was read, True, or not False.\n
                - `created_at` (str): Date time when was sent.\n
                - `type` (str): Model name which is related the notification.\n
                - `variable(equal to the value of type)` (object): Entire object which is related the notification.\n
                    - `field_1` (int): Field of object.\n
                    - `field_2` (str): Another Field of object.\n
                    - `etcetera`\n\n

            ### Response (Failure):\n
            - `404 Not Found`:
            Notifications not found.\n
            - `500 Internal Server Error`:
            If an unexpected error occurs.\n
        """
        try:
            if pk and pk.isdigit():
                noti = self.get_queryset(lookup=pk)

                if noti:
                    noti_serializer = self.serializer_class(instance=noti)
                    notifications_as_read.delay(
                        user=request.user.username, notifications=[noti.id])

                    return Response(noti_serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response({'detail': 'Notification not found.'}, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({'detail': 'Invalid notification id.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': f'Error on server side.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
