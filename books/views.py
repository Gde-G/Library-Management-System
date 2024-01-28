import operator
from functools import reduce

from django.db.models import Q
from rest_framework import viewsets
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.decorators import action

from drf_spectacular.utils import extend_schema, OpenApiParameter

from core.utils import GenericPagination
from core.serializers import DummySerializer, DetailSerializer

from .serializers import (
    ListAuthorSerializer, CreateAuthorSerializer, UpdateAuthorSerializer,
    BaseGenreSerializer, GenericGenreSerializer, BasePublisherSerializer,
    GenericPublisherSerializer, BaseBookSerializer, CreateBookSerializer, ListBookSerializer,
    UpdateBookSerializer
)
from .models import Author, Genre, Publisher, Book


class AuthorViewSet(viewsets.ModelViewSet):
    serializer_class = ListAuthorSerializer
    pagination_class = GenericPagination

    def get_serializer_class(self, *args, **kwargs):
        if self.action == 'list' or self.action == 'retrieve':
            return ListAuthorSerializer
        elif self.action == 'create':
            return CreateAuthorSerializer
        elif self.action == 'partial_update':
            return UpdateAuthorSerializer
        else:
            return DummySerializer

    def get_queryset(self, lookup=None, search: str = None, *args, **kwargs):
        if search and search != ' ':
            separate_search = list(map(str.lower, search.split(' ')))
            q_first_name = reduce(operator.or_, (Q(first_name__icontains=x)
                                                 for x in separate_search))
            q_last_name = reduce(operator.or_, (Q(last_name__icontains=x)
                                                for x in separate_search))
            authors = Author.objects.filter(
                q_first_name | q_last_name
            )
            return authors
        elif lookup:
            return Author.objects.filter(pk=lookup).first()
        else:
            return Author.objects.all().order_by('?')

    def get_permissions(self):
        if self.action == 'list' or self.action == 'retrieve':
            return [AllowAny(), ]
        else:
            return [IsAdminUser(), ]

    @extend_schema(
        responses={200: ListAuthorSerializer},
        parameters=[
            OpenApiParameter(
                name='search', description='Filtering by first_name/last_name content.', type=str),
            OpenApiParameter(
                name='page', description='Page number.', type=int),
            OpenApiParameter(
                name='page_size', description='Amount of results per page (max 30).', type=int),
        ],
    )
    def list(self, request: Request, *args, **kwargs):
        """
            List Authors.\n

            ### URL Parameters :\n
            - `search` (str): To find authors that contains in his body the "first_name/last_name".\n
            - `page` (int): Page to get.\n
            - `page_size` (int): Amount of authors to get.\n

            ### Response(Success):\n
            - `200 OK` : List of author objects.\n
                - `count` (int): Amount of TOTAL objects.\n
                - `next` (str): if exists, URL of the next objects, otherwise null.\n
                - `prev` (str):  if exists, URL of the previous objects, otherwise null.\n
                - `results` (array): List of objects.\n
                    - `id` (int): Author Identifier.\n
                    - `name` (str): Author First name + Last name.\n
                    - `biography` (str): Author Biography.\n
                    - `picture` (str): Path where is store the Author picture .\n
                    - `nationality` (str): ISO 3166-1 (alpha-2 code) of the Nationality.\n
                    - `birth_date` (str): Date of birth in format YYYY-mm-dd.\n
                    - `death_date` (str)(null): Date of death in the YYYY-mm-dd format. Otherwise, if is alive just leave it hanging in the void of null 😅.\n\n
            ### Response(Failure):\n
            - `404 Not Found`: 
            Author/s not be found.\n
        """

        search = self.request.GET.get('search', None)

        authors = self.get_queryset(search=search)
        if authors.exists():
            authors_serializer = self.get_serializer_class()(authors, many=True)
            paginator = self.pagination_class()
            paginated_data = paginator.paginate_queryset(
                authors_serializer.data,
                request,
                view=self
            )
            return paginator.get_paginated_response(paginated_data)

        return Response({'detail': 'Authors not found.'}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(responses={201: DetailSerializer})
    def create(self, request: Request, *args, **kwargs):
        """
            Create Author (Only Users with Admin Range).\n

            ### Request Body :\n
            - `id` (int): Author Identifier.\n
            - `first_name` (str): Author First name.\n
            - `last_name` (str): Author Last name.\n
            - `biography` (str): Author Biography.\n
            - `picture` (File): Binary for Author picture .\n
            - `nationality` (str)(optional): ISO 3166-1 (alpha-2 code) of the country.\n
            - `birth_date` (str): Date of birth in format YYYY-mm-dd.\n
            - `death_date` (str)(optional): Date of death in the YYYY-mm-dd format. Otherwise, if is alive just leave it hanging in the void of null 😅.\n\n

            ### Response(Success):\n
            - `201 Create` : List of author objects.\n
                - `detail` (str): Author successfully created.\n\n

            ### Response(Failure):\n
            - `400 BAD REQUEST`: 
            Invalid input data. Check the response for details.\n
            - `401 Unauthorized`:
            If the user is not authenticated.\n
        """

        author_serializer = self.get_serializer_class()(data=request.data)

        if author_serializer.is_valid():
            author_serializer.save()
            return Response({'detail': 'Author successfully created'}, status=status.HTTP_201_CREATED)
        else:
            return Response(author_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={200: ListAuthorSerializer}
    )
    def retrieve(self, request: Request, pk=None, *args, **kwargs):
        """
            Retrieve a single Author.\n

            ### Path Parameter:\n
            - `id` (int):
                The id of the author to get.\n\n
            ### Response(Success):\n
            - `200 OK` : List of author objects.\n
                - `id` (int): Author Identifier.\n
                - `name` (str): Author First name + Last name.\n
                - `biography` (str): Author Biography.\n
                - `picture` (str): Path where is store the Author picture .\n
                - `nationality` (str): ISO 3166-1 (alpha-2 code) of the Nationality.\n
                - `birth_date` (str): Date of birth in format YYYY-mm-dd.\n
                - `death_date` (str)(null): Date of death in the YYYY-mm-dd format. Otherwise, if is alive just leave it hanging in the void of null 😅.\n\n
            ### Response(Failure):\n
            - `400 BAD REQUEST`: 
            Pk not send or is invalid..\n
            - `404 Not Found`: 
            Author/s not be found.\n
        """

        if pk and pk.isdigit():
            try:
                author = self.get_queryset(lookup=int(pk))
            except ValueError:
                return Response({'detail': 'Pk parameter must be of base 10.'}, status=status.HTTP_400_BAD_REQUEST)
            if author:
                author_serializer = self.get_serializer_class()(instance=author)
                return Response(author_serializer.data, status=status.HTTP_200_OK)

            return Response({'detail': 'Author not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'detail': 'Pk not send or is invalid.'}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={405: DetailSerializer}
    )
    def update(self, request: Request, *args, **kwargs):
        ''' METHOD NOT ALLOWED.'''
        return Response({'detail': 'Method not allowed.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @extend_schema(responses={202: DetailSerializer})
    def partial_update(self, request: Request, pk=None, *args, **kwargs):
        """
            Update Author (Only Users with Admin Range).\n
            ### Path Parameter:\n
            - `id` (int):
                The id of the author to get.\n\n
            ### Request Body :\n
            - `first_name` (str)(option): Author First name.\n
            - `last_name` (str)(option): Author Last name.\n
            - `biography` (str)(option): Author Biography.\n
            - `picture` (str)(option): Path where is store the Author picture .\n
            - `nationality` (str)(optional): ISO 3166-1 (alpha-2 code) of the Nationality.\n
            - `birth_date` (str)(option): Date of birth in format YYYY-mm-dd.\n
            - `death_date` (str)(optional): Date of death in the YYYY-mm-dd format. Otherwise, if is alive just leave it hanging in the void of null 😅.\n\n

            ### Response(Success):\n
            - `202 Create` :\n
                - `detail` (str): Author successfully update.\n\n

            ### Response(Failure):\n
            - `400 BAD REQUEST`: 
            Invalid input data. Check the response for details.\n
            - `401 Unauthorized`:
            If the user is not authenticated.\n
            - `404 Not found`:
            If the user is not authenticated.\n
        """
        if pk and pk.isdigit():
            try:
                author = self.get_queryset(lookup=int(pk))
            except ValueError:
                return Response({'detail': 'Pk parameter must be of base 10.'}, status=status.HTTP_400_BAD_REQUEST)

            if author:
                author_serializer = self.get_serializer_class()(
                    instance=author,
                    data=request.data,
                    partial=True
                )
                if author_serializer.is_valid():
                    author_serializer.save()
                    return Response({'detail': 'Author be updated successfully.'}, status=status.HTTP_202_ACCEPTED)
                else:
                    return Response(author_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'detail': 'Author not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'detail': 'Pk not send.'}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={204: DummySerializer})
    def destroy(self, request: Request, pk=None, *args, **kwargs):
        """
            Delete Author (Only Users with Admin Range).\n

            ### Path Parameter:\n
            - `id` (int):
                The id of the author to get.\n\n
            ### Response(Success):\n
            - `204 Create` : Author be deleted.\n\n

            ### Response(Failure):\n
            - `400 BAD REQUEST`: 
            Invalid input data. Check the response for details.\n
            - `401 Unauthorized`:
            If the user is not authenticated.\n
            - `404 Not found`:
            If the user is not authenticated.\n
        """

        if pk and pk.isdigit():
            try:
                author = self.get_queryset(lookup=int(pk))
            except:
                return Response({'detail': 'Pk parameter must be of base 10.'}, status=status.HTTP_400_BAD_REQUEST)

            if author:
                author.delete()
                return Response({}, status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({'detail': 'Author not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'detail': 'Pk not send.'}, status=status.HTTP_400_BAD_REQUEST)


class GenreViewSet(viewsets.ModelViewSet):
    serializer_class = BaseGenreSerializer
    pagination_class = GenericPagination
    lookup_field = 'slug'

    def get_queryset(self, lookup=None, search: str = None):
        if search and search != ' ':
            separate_search = search.split(' ')
            q_name = reduce(
                operator.or_,
                (Q(name__icontains=x) for x in separate_search))
            q_description = reduce(
                operator.or_,
                (Q(description__icontains=x) for x in separate_search))

            genres = Genre.objects.filter(
                q_name | q_description
            ).order_by('-name')
            return genres
        if lookup:
            return Genre.objects.filter(slug=lookup).first()

        return Genre.objects.all().order_by('-name')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return GenericGenreSerializer
        else:
            return self.serializer_class

    def get_permissions(self):
        if self.action == 'list' or self.action == 'retrieve':
            return [AllowAny(), ]
        else:
            return [IsAdminUser(), ]

    @extend_schema(
        responses={200: serializer_class},
        parameters=[
            OpenApiParameter(
                name='search', description='Filtering by name/description content.', type=str),
            OpenApiParameter(
                name='page', description='Page number.', type=int),
            OpenApiParameter(
                name='page_size', description='Amount of results per page (max 30).', type=int),
        ],
    )
    def list(self, request, *args, **kwargs):
        """
            List Genres.\n

            ### URL Parameters :\n
            - `search` (str): To find Genres that contains in his body the "first_name/last_name".\n
            - `page` (int): Page to get.\n
            - `page_size` (int): Amount of Genres to get per page.\n

            ### Response(Success):\n
            - `200 OK` : List of Genres objects.\n
                - `count` (int): Amount of TOTAL objects.\n
                - `next` (str): if exists, URL of the next objects, otherwise null.\n
                - `prev` (str): if exists, URL of the previous objects, otherwise null.\n
                - `results` (array): List of objects.\n
                    - `name` (str): Genre name.\n
                    - `description` (str): Genre Description.\n
                    - `slug` (str): Genre slug.\n
            ### Response(Failure):\n
            - `404 Not Found`: 
            Genre/s not be found.\n
        """

        search = self.request.GET.get('search', None)

        genres = self.get_queryset(search=search)
        if genres.exists():
            genres_serializer = self.serializer_class(genres, many=True)

            paginator = self.pagination_class()
            paginator_data = paginator.paginate_queryset(
                genres_serializer.data,
                request,
                view=self
            )
            return paginator.get_paginated_response(paginator_data)
        else:
            return Response({'detail': 'Genres not found.'}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(responses={201: DetailSerializer})
    def create(self, request, *args, **kwargs):
        """
            Create Genre (Only Users with Admin Range).\n

            ### Request Body :\n
            - `name` (str): Genre name.\n
            - `description` (str): Genre description.\n

            ### Response(Success):\n
            - `201 Create` : List of Genre objects.\n
                - `detail` (str): Genre successfully created.\n\n

            ### Response(Failure):\n
            - `400 BAD REQUEST`: 
            Invalid input data. Check the response for details.\n
            - `401 Unauthorized`:
            If the user is not authenticated.\n
        """
        genre_serializer = self.serializer_class(data=request.data)

        if genre_serializer.is_valid():
            genre_serializer.save()

            return Response({'detail': 'Genre created successfully.'}, status=status.HTTP_201_CREATED)
        else:
            return Response(genre_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={200: BaseBookSerializer})
    def retrieve(self, request, *args, **kwargs):
        """
            Retrieve Genre.\n
            ### Path Parameter:\n
            - `slug` (str):
                The slug of the genre to get.\n\n
            ### Response(Success):\n
            - `200 OK` : Genre object.\n
                - `name` (str): Genre name.\n
                - `description` (str): Genre Description.\n

            ### Response(Failure):\n
            - `404 Not Found`: 
            Genre/s not be found.\n
        """
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Method not allowed."""
        return Response({'detail': 'Method not allowed.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @extend_schema(responses={202: DetailSerializer})
    def partial_update(self, request, slug=None, *args, **kwargs):
        """
            Update Genre (Only Users with Admin Range).\n

            ### Path Parameter:\n
            - `slug` (str):
                The id of the slug of genre to update.\n\n
            ### Request Body :\n
            - `name` (str): Genre name.\n
            - `description` (str): Genre description.\n

            ### Response(Success):\n
            - `202 ACCEPTED` : \n
                - `detail` (str): Genre updated successfully.\n\n

            ### Response(Failure):\n
            - `400 BAD REQUEST`: 
            Invalid input data. Check the response for details.\n
            - `401 Unauthorized`:
            If the user is not authenticated.\n
            - `404 Not found`:
            Genre not found.\n
        """

        if slug:
            genre = self.get_queryset(lookup=slug)
            if genre:
                genre_serializer = self.get_serializer_class()(
                    instance=genre, data=request.data, partial=True)
                if genre_serializer.is_valid():
                    genre_serializer.save()
                    return Response({'detail': 'Genre updated successfully.'}, status=status.HTTP_202_ACCEPTED)
                else:
                    return Response(genre_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'detail': 'Genre not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'detail': 'Invalid pk.'}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={204: DummySerializer})
    def destroy(self, request, *args, **kwargs):
        """
            Delete Genre (Only Users with Admin Range).\n

            ### Path Parameter:\n
            - `slug` (str):
                The slug of the Genre to delete.\n\n
            ### Response(Success):\n
            - `204 Create` : Genre was deleted.\n\n

            ### Response(Failure):\n
            - `400 BAD REQUEST`: 
            Invalid input data. Check the response for details.\n
            - `401 Unauthorized`:
            If the user is not authenticated.\n
            - `404 Not found`:
            If the user is not authenticated.\n
        """
        return super().destroy(request, *args, **kwargs)


class PublisherViewSet(viewsets.ModelViewSet):
    serializer_class = BasePublisherSerializer
    pagination_class = GenericPagination

    def get_queryset(self, lookup=None, search=None):
        if search and search != ' ':
            separate_search = search.split(' ')
            q_name = reduce(operator.or_, (Q(name__icontains=x)
                            for x in separate_search))

            return Publisher.objects.filter(q_name).order_by('-name')
        if lookup:
            return Publisher.objects.filter(id=lookup).first()

        return Publisher.objects.all().order_by('-name')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return GenericPublisherSerializer
        else:
            return self.serializer_class

    def get_permissions(self):
        if self.action == 'list' or self.action == 'retrieve':
            return [AllowAny(), ]
        else:
            return [IsAdminUser(), ]

    @extend_schema(responses={201: DetailSerializer})
    def create(self, request, *args, **kwargs):
        """
            Create Publisher (Only Users with Admin Range).\n

            ### Request Body :\n
            - `name` (str): Publisher name.\n
            - `country` (str): ISO 3166, country where is located the Publisher .\n

            ### Response(Success):\n
            - `201 CREATED` : \n
                - `detail` (str): Publisher created successfully. \n\n

            ### Response(Failure):\n
            - `400 BAD REQUEST`: 
            Invalid input data. Check the response for details.\n
            - `401 Unauthorized`:
            If the user is not authenticated.\n

        """
        publisher_serializer = self.serializer_class(data=request.data)

        if publisher_serializer.is_valid():
            publisher_serializer.save()

            return Response({'detail': 'Publisher created successfully.'}, status=status.HTTP_201_CREATED)
        else:
            return Response(publisher_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={200: serializer_class},
        parameters=[
            OpenApiParameter(
                name='search', description='Filtering by name/description content.', type=str),
            OpenApiParameter(
                name='page', description='Page number.', type=int),
            OpenApiParameter(
                name='page_size', description='Amount of results per page (max 30).', type=int),
        ],
    )
    def list(self, request, *args, **kwargs):
        """
            List Publishers.\n

            ### URL Parameters :\n
            - `search` (str): To find Publishers that contains in his name.\n
            - `page` (int): Page to get.\n
            - `page_size` (int): Amount of Publishers to get per page.\n

            ### Response(Success):\n
            - `200 OK` : List of Publishers objects.\n
                - `count` (int): Amount of TOTAL objects.\n
                - `next` (str): if exists, URL of the next objects, otherwise null.\n
                - `prev` (str): if exists, URL of the previous objects, otherwise null.\n
                - `results` (array): List of objects.\n
                    - `name` (str): Publisher name.\n
                    - `country` (str): Publisher Description.\n
                    - `id` (int): Publisher Identifier.\n
            ### Response(Failure):\n
            - `404 Not Found`: 
            Publisher/s not be found.\n
        """
        search = self.request.GET.get('search', None)

        publishers = self.get_queryset(search=search)
        if publishers.exists():
            publishers_serializer = self.serializer_class(
                publishers, many=True)
            paginator = self.pagination_class()
            paginated_data = paginator.paginate_queryset(
                publishers_serializer.data,
                request,
                view=self
            )

            return paginator.get_paginated_response(paginated_data)
        else:
            return Response({'detail': 'Publishers not found.'}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(responses={200: BasePublisherSerializer})
    def retrieve(self, request, *args, **kwargs):
        """
            Retrieve Publisher.\n
            ### Path Parameter:\n
            - `id` (int):
                The id of the Publisher to get.\n\n
            ### Response(Success):\n
            - `200 OK` : Publisher object.\n
                - `name` (str): Publisher name.\n
                - `country` (str)(optional): ISO 3166, country where is located the Publisher .\n
                - `id` (int): Publisher Identifier.\n

            ### Response(Failure):\n
            - `404 Not Found`: 
            Publisher not be found.\n
        """
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(request=DummySerializer, responses={405: DummySerializer})
    def update(self, request, *args, **kwargs):
        """Method not allowed."""
        return Response({'detail': 'Method not allowed.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @extend_schema(responses={202: DetailSerializer})
    def partial_update(self, request, pk=None, *args, **kwargs):
        """
            Update Publisher (Only Users with Admin Range).\n
            ### Path Parameter:\n
            - `id` (int):
                The id of the Publisher to get.\n\n
            ### Request Body :\n
            - `name` (str)(optional): Publisher name.\n
            - `country` (str)(optional): ISO 3166, country where is located the Publisher .\n

            ### Response(Success):\n
            - `202 ACCEPTED` : \n
                - `detail` (str): Publisher updated successfully. \n\n

            ### Response(Failure):\n
            - `400 BAD REQUEST`: 
            Invalid input data. Check the response for details.\n
            - `401 Unauthorized`:
            If the user is not authenticated.\n
            - `404 Not found`:
            Publisher not found.\n
        """
        if pk and pk.isdigit():
            publisher = self.get_queryset(lookup=int(pk))
            if publisher:
                publisher_serializer = self.get_serializer_class()(
                    instance=publisher, data=request.data, partial=True)
                if publisher_serializer.is_valid():
                    publisher_serializer.save()
                    return Response({'detail': 'Publisher update successfully.'}, status=status.HTTP_202_ACCEPTED)
                else:
                    return Response(publisher_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'detail': 'Publisher not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'detail': 'Invalid pk.'}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={204: DummySerializer})
    def destroy(self, request, *args, **kwargs):
        """
            Delete Publisher (Only Users with Admin Range).\n

            ### Path Parameter:\n
            - `id` (int):
                The id of the Publisher to get.\n\n
            ### Response(Success):\n
            - `204 Create` : Publisher be deleted.\n\n

            ### Response(Failure):\n
            - `400 BAD REQUEST`: 
            Invalid input data. Check the response for details.\n
            - `401 Unauthorized`:
            If the user is not authenticated.\n
            - `404 Not found`:
            If the user is not authenticated.\n
        """
        return super().destroy(request, *args, **kwargs)


class BookViewSet(viewsets.ModelViewSet):
    serializer_class = BaseBookSerializer
    pagination_class = GenericPagination
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateBookSerializer
        elif self.action in ['list', 'retrieve', 'list_books_by_author', 'list_books_by_genre', 'list_books_by_publisher']:
            return ListBookSerializer
        elif self.action == 'partial_update':
            return UpdateBookSerializer

        return super().get_serializer_class()

    def get_queryset(self, lookup=None, search=None, author=None, genre=None, publisher=None):
        if search and search != ' ':
            separate_search = search.split(' ')

            q_title = reduce(
                operator.or_, (Q(title__icontains=x) for x in separate_search)
            )
            q_genre = reduce(
                operator.or_, (Q(genre__name__icontains=x)
                               for x in separate_search)
            )
            q_publisher = reduce(
                operator.or_, (Q(publisher__name__icontains=x)
                               for x in separate_search)
            )

            return Book.objects.select_related('author', 'publisher', 'genre').filter(
                q_title | q_genre | q_publisher).order_by('-title', '-publication_date')

        if lookup:
            return Book.objects.select_related('author', 'publisher', 'genre').filter(
                Q(slug__exact=lookup)
            ).first()

        if author:
            return Book.objects.select_related('author', 'publisher', 'genre').filter(author=author).order_by('-title', '-publication_date')

        if genre:
            return Book.objects.select_related('author', 'publisher', 'genre').filter(genre=genre).order_by('-title', '-publication_date')

        if publisher:
            return Book.objects.select_related('author', 'publisher', 'genre').filter(publisher=publisher).order_by('-title', '-publication_date')

        return Book.objects.select_related('author', 'publisher', 'genre').all().order_by('-title', '-publication_date')

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser(), ]
        else:
            return [AllowAny(), ]

    @extend_schema(responses={201: DetailSerializer})
    def create(self, request, *args, **kwargs):
        """
            Create Book (Only Users with Admin Range).\n

            ### Request Body :\n
            - `title` (str): Book Title.\n
            - `language` (str): Language in which the book is written.\n
            - `edition` (int): Number of edition.\n
            - `amount_pages` (int): Number of pages the book has.\n
            - `cover` (file): Binary forCover of the book.\n
            - `publication_date` (str): Date when it was published in YYYY-mm-dd format.\n
            - `genre` (str): Genre slug to which it belongs.\n
            - `publisher` (int)(optional): Publisher id to which it belongs, if unknown put null.\n
            - `author` (int)(optional): Author id to which it belongs, if unknown put null.\n

            ### Response(Success):\n
            - `201 CREATED` : \n
                - `detail` (str): Book created successfully. \n\n

            ### Response(Failure):\n
            - `400 BAD REQUEST`: 
            Invalid input data. Check the response for details.\n
            - `401 Unauthorized`:
            If the user is not authenticated.\n

        """
        book_serializer = self.get_serializer_class()(data=request.data)
        if book_serializer.is_valid():
            book_serializer.save()
            return Response({'detail': 'Book created successfully.'}, status=status.HTTP_201_CREATED)
        else:
            return Response(book_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={200: ListBookSerializer},
        parameters=[
            OpenApiParameter(
                name='search', description='Filtering by title content.', type=str),
            OpenApiParameter(
                name='page', description='Page number.', type=int),
            OpenApiParameter(
                name='page_size', description='Amount of results per page (max 30).', type=int),
        ],
    )
    def list(self, request: Request, *args, **kwargs):
        """
            List Books.\n

            ### URL Parameters :\n
            - `search` (str): To find books that contains in his title the content.\n
            - `page` (int): Page to get.\n
            - `page_size` (int): Amount of books to get epr page.\n

            ### Response(Success):\n
            - `200 OK` : \n
                - `count` (int): TOTAL Amount of Books.\n
                - `next` (str): if exists, URL of the next objects, otherwise null.\n
                - `prev` (str): if exists, URL of the previous objects, otherwise null.\n
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
            - `404 NOT FOUND`: 
            Book/s Not found.\n
        """
        search_param = request.query_params.get('search', None)

        books = self.get_queryset(search=search_param)

        if books.exists():
            books_serializer = self.get_serializer_class()(books, many=True)
            paginator = self.pagination_class()
            paginator_data = paginator.paginate_queryset(
                books_serializer.data,
                request,
                view=self
            )
            return paginator.get_paginated_response(paginator_data)
        else:
            return Response({'detail': 'Books not found.'}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(responses={200: ListBookSerializer})
    def retrieve(self, request, lookup=None, *args, **kwargs):
        """
            Retrieve Book.\n
            ### Path Parameter:\n
            - `slug` (str):
                The slug of the book to get.\n\n
            ### Response(Success):\n
            - `200 OK` : \n
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
            - `404 NOT FOUND`: 
            Book Not found.\n
        """
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(request=DummySerializer, responses={405: DetailSerializer})
    def update(self, request, *args, **kwargs):
        '''### Method not allowed.'''
        return Response({'detail': 'HTTP PUT method is not allowed, instead use PATCH.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @extend_schema(responses={202: UpdateBookSerializer})
    def partial_update(self, request, slug=None, *args, **kwargs):
        """
            Update Book (Only Users with Admin Range).\n
            ### Path Parameter:\n
            - `slug` (str):
                The slug of the Book to get.\n\n
            ### Request Body :\n
            - `title` (str)(optional): Book Title.\n
            - `language` (str)(optional): Language in which the book is written.\n
            - `edition` (int)(optional): Number of edition.\n
            - `amount_pages` (int)(optional): Number of pages the book has.\n
            - `cover` (file)(optional): Binary forCover of the book.\n
            - `publication_date` (str)(optional): Date when it was published in YYYY-mm-dd format.\n
            - `genre` (str)(optional): Genre slug to which it belongs.\n
            - `publisher` (int)(optional): Publisher id to which it belongs, if unknown put null.\n
            - `author` (int)(optional): Author id to which it belongs, if unknown put null.\n

            ### Response(Success):\n
            - `202 ACCEPTED` : \n
                - `detail` (str): Book updated successfully. \n\n

            ### Response(Failure):\n
            - `400 BAD REQUEST`: 
            Invalid input data. Check the response for details.\n
            - `401 Unauthorized`:
            If the user is not authenticated.\n
            - `404 Not found`:
            Book not found.\n
        """

        if slug:
            book = self.get_queryset(lookup=slug)
            if book:
                book_serializer = self.get_serializer_class()(
                    instance=book, data=request.data, partial=True)
                if book_serializer.is_valid():
                    book_serializer.save()

                    return Response({'detail': 'Book updated successfully.'}, status=status.HTTP_202_ACCEPTED)
                else:
                    return Response(book_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'detail': 'Book not found.'}, status=status.HTTP_404_NOT_FOUND)

        else:
            return Response({'detail': 'Slug of the book must be provided.'}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={204: DummySerializer})
    def destroy(self, request, slug=None, *args, **kwargs):
        """
            Delete Book (Only Users with Admin Range).\n

            ### Path Parameter:\n
            - `slug` (str):
                The slug of the Book to get.\n\n
            ### Response(Success):\n
            - `204 Create` : Book be deleted.\n\n

            ### Response(Failure):\n
            - `400 BAD REQUEST`: 
            Invalid input data. Check the response for details.\n
            - `401 Unauthorized`:
            If the user is not authenticated.\n
            - `404 Not found`:
            Book not found.\n
        """

        if slug:
            book = self.get_queryset(lookup=slug)
            if book:
                book.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            else:
                return Response({'detail': 'Book not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'detail': 'Slug of the book must be provided.'}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={200: ListBookSerializer},
        parameters=[
            OpenApiParameter(
                name='page', description='Page number.', type=int),
            OpenApiParameter(
                name='page_size', description='Amount of results per page (max 30).', type=int),
        ],
    )
    @action(methods=['GET'], detail=False, url_path="author/(?P<pk>[^/.]+)", url_name='list-by-author')
    def list_books_by_author(self, request, pk=None, *args, **kwargs):
        """
            List Books by Author.\n

            ### Path Parameter:\n
            - `id` (int):
                The id of the Author to get his Books.\n\n
            ### URL Parameters :\n
            - `page` (int): Page to get.\n
            - `page_size` (int): Amount of books to get per page.\n

            ### Response(Success):\n
            - `200 OK` : \n
                - `count` (int): TOTAL Amount of Books.\n
                - `next` (str): if exists, URL of the next objects, otherwise null.\n
                - `prev` (str): if exists, URL of the previous objects, otherwise null.\n
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
            - `404 NOT FOUND`: 
            Book/s of this author Not found.\n
        """
        if pk and pk.isdigit():
            books = self.get_queryset(author=pk)
            if books.exists():
                books_serializer = self.get_serializer_class()(books, many=True)
                paginator = self.pagination_class()
                paginated_data = paginator.paginate_queryset(
                    books_serializer.data,
                    request,
                    view=self
                )
                return paginator.get_paginated_response(paginated_data)
            else:
                return Response({'detail': "Books of the author received, not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'detail': 'Invalid pk.'}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={200: ListBookSerializer},
        parameters=[
            OpenApiParameter(
                name='page', description='Page number.', type=int),
            OpenApiParameter(
                name='page_size', description='Amount of results per page (max 30).', type=int),
        ],
    )
    @action(methods=['GET'], detail=False, url_path="genre/(?P<slug>[^/.]+)", url_name='list-by-genre')
    def list_books_by_genre(self, request, slug=None, *args, **kwargs):
        """
            List Books by Genre.\n

            ### Path Parameter:\n
            - `slug` (str):
                The slug of the Genre to get his Books.\n\n
            ### URL Parameters :\n
            - `page` (int): Page to get.\n
            - `page_size` (int): Amount of book to get per page.\n

            ### Response(Success):\n
            - `200 OK` : \n
                - `count` (int): TOTAL Amount of Books.\n
                - `next` (str): if exists, URL of the next objects, otherwise null.\n
                - `prev` (str): if exists, URL of the previous objects, otherwise null.\n
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
            - `404 NOT FOUND`: 
            Book/s of this author Not found.\n
        """
        if slug and slug != ' ':
            books = self.get_queryset(genre=slug)
            if books.exists():
                books_serializer = self.get_serializer_class()(books, many=True)
                paginator = self.pagination_class()
                paginated_data = paginator.paginate_queryset(
                    books_serializer.data,
                    request,
                    view=self
                )
                return paginator.get_paginated_response(paginated_data)
            else:
                return Response({'detail': 'Books of the genre received, not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'detail': 'Invalid slug.'}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={200: ListBookSerializer},
        parameters=[
            OpenApiParameter(
                name='page', description='Page number.', type=int),
            OpenApiParameter(
                name='page_size', description='Amount of results per page (max 30).', type=int),
        ],
    )
    @action(methods=['GET'], detail=False, url_path="publisher/(?P<pk>[^/.]+)",  url_name='list-by-publisher')
    def list_books_by_publisher(self, request, pk=None, *args, **kwargs):
        """
            List Books by Publisher.\n

            ### Path Parameter:\n
            - `id` (int):
                The id of the Publisher to get his Books.\n\n
            ### URL Parameters :\n
            - `page` (int): Page to get.\n
            - `page_size` (int): Amount of books to get per page.\n

            ### Response(Success):\n
            - `200 OK` : \n
                - `count` (int): TOTAL Amount of Books.\n
                - `next` (str): if exists, URL of the next objects, otherwise null.\n
                - `prev` (str): if exists, URL of the previous objects, otherwise null.\n
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
            - `404 NOT FOUND`: 
            Book/s of this publisher Not found.\n
        """
        if pk and pk.isdigit():
            books = self.get_queryset(publisher=pk)
            if books.exists():
                books_serializer = self.get_serializer_class()(books, many=True)
                paginator = self.pagination_class()
                paginated_data = paginator.paginate_queryset(
                    books_serializer.data,
                    request,
                    view=self
                )
                return paginator.get_paginated_response(paginated_data)
            else:
                return Response({'detail': "Books of the author received, not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'detail': 'Invalid pk.'}, status=status.HTTP_400_BAD_REQUEST)
