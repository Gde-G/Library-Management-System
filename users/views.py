from datetime import timedelta

from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.utils import timezone
from django.db.models import Q
from django.db import transaction
from django.contrib.sites.shortcuts import get_current_site


from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser

from drf_spectacular.utils import OpenApiParameter, extend_schema

from core.utils import GenericPagination
from core.serializers import DummySerializer
from .serializers import (
    CreateUserSerializer, ListProfileUserSerializer,
    ListSimpleUserSerializer, UpdateUserSerializer, PasswordCheckMatchSerializer,
    PasswordChangeSerializer, PasswordRecoveryRequestSerializer,
    PasswordRecoveryConfirmSerializer
)

from .models import User, ResetLink
from .tokens import account_activation_token
from .utils import generate_available_username_suggestions
from .tasks import send_email


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = CreateUserSerializer
    lookup_field = 'username'
    pagination_class = GenericPagination

    def get_serializer_class(self):
        """
            Get the serializer class based on the action.

            - For 'create', use CreateUserSerializer.
            - For 'list', use ListSimpleUserSerializer.
            - For 'retrieve', use ListProfileUserSerializer.
            - For 'partial_update' or 'update', use UpdateUserSerializer.
        """
        if self.action == 'create':
            return CreateUserSerializer
        elif self.action == 'list':
            return ListSimpleUserSerializer
        elif self.action == 'retrieve':
            return ListProfileUserSerializer
        elif self.action == 'partial_update' or self.action == 'update':
            return UpdateUserSerializer

        return super().get_serializer_class()

    def get_queryset(self, lookup=None, search=None, *args, **kwargs):

        if search:
            users = self.serializer_class.Meta.model.objects.filter(
                Q(username__icontains=search) &
                Q(username__icontains=search) &
                Q(is_active=True)
            )

        elif lookup == None:
            users = self.serializer_class.Meta.model.objects.filter(
                Q(is_active=True)
            )
        else:
            users = self.serializer_class.Meta.model.objects.filter(
                Q(username=lookup) &
                Q(is_active=True)
            ).first()

        return users

    def get_permissions(self):
        if self.action == 'list':
            return [IsAdminUser(),]
        if self.action in ['retrieve', 'update', 'partial_update']:
            return [IsAuthenticated(), ]
        else:
            return [AllowAny(), ]

    @extend_schema(
        responses={200: ListSimpleUserSerializer(many=True)},
        parameters=[
            OpenApiParameter(
                name='search', description='Filtering by username and username.', type=str),
            OpenApiParameter(
                name='page', description='Page number.', type=int),
            OpenApiParameter(
                name='page_size', description='Amount of results per page.', type=int),
        ],
    )
    def list(self, request: Request, *args, **kwargs):
        """
            List users.\n

            ### URL Parameters :\n
            - `search` (str): To find posts that contains in his body the "value".\n
            - `page` (int): Page to get.\n
            - `page_size` (int): Amount of posts to get.\n

            ### Response(Success):\n
            - `200 OK` : List of user objects.\n
                - `username` (str): User handle.\n
                - `username` (str): Username.\n
                - `profile_img` (str): URL to the user's profile image.\n
                - `biography` (str): Profile Biography.\n
                - `follower_amount` (int): Number of followers for the user.\n
                - `following_amount` (int): Number of users the user is following.\n\n

            ### Response(Failure):\n
            - `401 Unauthorized`: 
            If the user is not authenticated.\n
            - `404 Not Found`: 
            Users not be found.\n
        """

        lookup_search = self.request.GET.get('search', None)

        users = self.get_queryset(search=lookup_search)
        if users.exists():
            users_serializer = self.get_serializer_class()(users, many=True)
            paginator = self.pagination_class()
            paginated_data = paginator.paginate_queryset(
                users_serializer.data, request, view=self)

            return paginator.get_paginated_response(paginated_data)
        else:
            return Response({'detail': 'Not found users.'}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request: Request, *args, **kwargs):
        """
        Create a new user.\n

        Creation of a new user account. Upon successful creation,
        an activation email is sent to the user's email address to complete the registration process.\n\n

        ## Fields (in the Request Body):\n
        - ### Required:
            - `username` (str): Username for the user.\n
            - `email` (str): Email address for the user.\n
            - `password` (str): User's password.\n
            - `password2` (str): Confirmation of the user's password.\n
            - `first_name` (str): User's first name.\n
            - `last_name` (str): User's last name.\n

        - ### Optionals:\n
            - `profile_img` (file): Profile image for the user.\n
            - `birth_date` (str): User's date of birth.\n\n

        ### Response (Success):\n
        - 201 Created: User created successfully. An activation email will be sent to the user's email address.\n\n

        ### Response (Failure):\n
        - 400 Bad Request: Invalid input data. Check the response for details.\n
        - 409 Conflict: Unable to send the activation email.
        """
        user_serializer = self.serializer_class(data=request.data)
        if user_serializer.is_valid():
            user = user_serializer.save()

            try:

                transaction.on_commit(
                    lambda: send_email.apply_async(
                        args=[
                            get_current_site(request).domain,
                            request.is_secure(),
                            user.username,
                            user.email,
                            "Welcome to Library Management System - Confirm sing up.",
                            'email_confirmation_message.html'
                        ],
                        countdown=10
                    )
                )

                return Response({'message': f'User created successfully. Check the inbox of {user.email} to activate your account.'}, status=status.HTTP_201_CREATED)
            except:
                return Response(
                    {'message': f'Impossible to send the email to {user.email}.'},
                    status=status.HTTP_409_CONFLICT
                )
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(parameters=[OpenApiParameter("username", str, OpenApiParameter.PATH)])
    def update(self, request: Request, username=None, *args, **kwargs):
        """
        Update user information.\n

        Update of user information. To update the information,
        the user must be authenticated and can only update their own account.\n

        ### Path Parameter:\n
        - `username` (str): The handle of the user account to be updated.\n\n

        ### Request Body (Partial Update):\n
        - The request body should contain the fields to be updated. Partial updates are allowed.\n
            - `username` (str): Username for the user.\n
            - `email` (str): Email address for the user.\n
            - `first_name` (str): User's first name.\n
            - `last_name` (str): User's last name.\n
            - `profile_img` (file): Profile image for the user.\n
            - `birth_date` (str): User's date of birth.\n\n

        ### Response (Success):\n
        - `200 OK`:
        User information updated successfully.\n
            - `message` (str): Confirmation message.\n\n

        ### Response (Failure):\n
        - `400 Bad Request`:
        Invalid input data. Check the response for details.\n
        - `403 Forbidden`:
        The user is not allowed to update the account.\n
        """
        user = self.get_queryset(lookup=username)

        if request.user == user:
            try:
                user_serializer = self.get_serializer_class()
                user_serializer = user_serializer(
                    user, data=request.data, partial=True)

                if user_serializer.is_valid():

                    user = user_serializer.save()

                    return Response(data={'message': 'User update successfully.'}, status=status.HTTP_200_OK)
                else:
                    return Response(data=user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except:
                return Response({'error': "Internal Error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({'error': 'Not allow access.'}, status=status.HTTP_403_FORBIDDEN)

    @extend_schema(parameters=[OpenApiParameter("username", str, OpenApiParameter.PATH)])
    def partial_update(self, request, username=None, *args, **kwargs):
        """
        Update user information.\n

        Update of user information. To update the information,
        the user must be authenticated and can only update their own account.\n

        ### Path Parameter:\n
        - `username` (str): The handle of the user account to be updated.\n\n

        ### Request Body (Partial Update):\n
        - The request body should contain the fields to be updated. Partial updates are allowed.\n
            - `username` (str): Username for the user.\n
            - `username` (str): Unique user handle.\n
            - `email` (str): Email address for the user.\n
            - `first_name` (str): User's first name.\n
            - `last_name` (str): User's last name.\n
            - `gender` (str): User's gender.\n
            - `biography` (str): User's biography.\n
            - `profile_img` (file): Profile image for the user.\n
            - `header_photo` (file): Header photo for the user profile.\n
            - `email_substitute` (str): Substitute email address for communication.\n
            - `website` (str): User's website URL.\n
            - `location` (str): User's location.\n
            - `birth_date` (str): User's date of birth.\n\n

        ### Response (Success):\n
        - `200 OK`:
        User information updated successfully.\n
            - `message` (str): Confirmation message.\n\n

        ### Response (Failure):\n
        - `400 Bad Request`:
        Invalid input data. Check the response for details.\n
        - `403 Forbidden`:
        The user is not allowed to update the account.\n
        """

        kwargs['partial'] = True
        return self.update(request, username=username, *args, **kwargs)

    @extend_schema(parameters=[OpenApiParameter("username", str, OpenApiParameter.PATH)])
    def retrieve(self, request: Request, *args, **kwargs):
        """
        Retrieve user profile.\n

        Retrieval of a user's profile information find it from the username. The user must be authenticated to access this endpoint.\n\n
        ### Path Parameter:\n
        - `username` (str):
        The handle of the user account to get the profile.\n\n

        ### Response (Success):\n
        - `200 OK`: 
        User profile retrieved successfully.\n
            - `username` (str): User's username.\n
            - `username` (str): User's unique handle.\n
            - `email` (str): User's email address.\n
            - `first_name` (str): User's first name.\n
            - `last_name` (str): User's last name.\n
            - `birth_date` (str): User's date of birth.\n
            - `biography` (str): User's biography.\n
            - `profile_img` (str): URL to the user's profile image.\n
            - `header_photo` (str): URL to the user's header photo.\n
            - `website` (str): User's website URL.\n
            - `location` (str): User's location.\n
            - `create_at` (str): Formatted creation date (e.g., "January of 2022").\n
            - `follower_amount` (int): Number of followers for the user.\n
            - `following_amount` (int): Number of users the user is following.\n\n

        ### Response (Failure):\n
        - `401 Unauthorized`:
        User not authenticated.\n
        -`403 FORBIDDEN`:
        The authenticated user not have permission. access denied.\n
        - `404 Not Found`:
        User with the username parse in the query parameter not exists or is inactive.\n
        """
        if request.user.is_authenticated:

            return super().retrieve(request, *args, **kwargs)
        else:
            return Response({'detail': 'Not authenticated user.'}, status=status.HTTP_401_UNAUTHORIZED)

    @extend_schema(parameters=[OpenApiParameter("username", str, OpenApiParameter.PATH)])
    def destroy(self, request: Request, username=None, *args, **kwargs):
        """
        Deactivate user account.\n

        Deactivation of a user account. To deactivate the account,
        the user must be authenticated and can only deactivate their own account.\n

        ### Path Parameter:\n
        - `username` (str):
        The handle of the user account to be deactivated.\n\n

        ### Response (Success):\n
        - `200 OK`:
        User account deactivated successfully.\n
            - `message` (str): Confirmation message.\n\n

        ### Response (Failure):\n
        - `403 Forbidden`:
        The user is not allowed to deactivate the account.\n
    """
        user = self.get_queryset(lookup=username)
        if request.user == user:
            try:
                user.is_active = False
                user.save()
                return Response({'message': 'User has been deleted.'}, status=status.HTTP_200_OK)
            except:
                return Response({'error': "Something fail."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({'error': 'Not allow access.'}, status=status.HTTP_403_FORBIDDEN)

    @extend_schema(
        request=DummySerializer,
        responses={200: DummySerializer},
        parameters=[
            OpenApiParameter("field_name", str, OpenApiParameter.PATH),
            OpenApiParameter("value", str, OpenApiParameter.PATH)
        ]
    )
    @action(
        methods=['GET'], detail=False,
        url_path=r'check-field-availability/(?P<field_name>[^/.]+)/(?P<value>[\w.@+-]+)',
    )
    def check_field_value_availability(self, request: Request, field_name=None, value=None):
        """
        Check the availability of a field value.\n

        Checking the availability of a specific field value(email, username) for user registration.\n
        The field_name and value are provided as path parameters.\n

        ### Path Parameters:\n
        - `field_name` (str): The name of the field to check ('username', 'email').\n
        - `value` (str): The value to check for availability.\n\n

        ### Request:\n
        - The request body is not required.\n\n

        ### Response (Success):\n
        - `200 OK`:
        Field value availability checked successfully.\n
            - `available` (bool): Indicates whether the field value is available or not.\n
            - `message` (str): Indicates that the field_name field with that value already exists.\n
            - `suggestions` (list of str, optional): Suggestions for available usernames (if applicable).\n\n

        ### Response (Failure):\n
        - `400 BAD REQUEST`:
        If the field_name is different than username or email.\n

        """
        field_name = field_name.lower()
        if field_name in ['username', 'email']:
            value = value.lower()
            data = {field_name: value}
            try:
                User.objects.get(**data)
                if field_name == 'email':
                    return Response(
                        {
                            'available': False,
                            'message': 'Already exists an user with this email.'
                        },
                        status=status.HTTP_200_OK
                    )
                return Response(
                    {
                        'available': False,
                        'message': 'Already exists an user with this username.',
                        'suggestions': generate_available_username_suggestions(value)
                    },
                    status=status.HTTP_200_OK
                )
            except User.DoesNotExist:
                return Response({'available': True}, status=status.HTTP_200_OK)
        else:
            return Response({'field_name': 'Must be email or username.'}, status=status.HTTP_400_BAD_REQUEST)


class PasswordsCheckMatchView(GenericAPIView):

    serializer_class = PasswordCheckMatchSerializer

    def post(self, request):
        """
        Checking if passwords match.\n

        ### Request:\n
        - `password` (str): The first password.\n
        - `password2` (str): The second password for comparison.\n\n

        ### Response (Success):\n
        - `200 OK`:
        Passwords match.\n
            - `match` (bool): True if the passwords match, False otherwise.\n\n

        ### Response (Failure):\n
        - `400 Bad Request`:
        If the request data is invalid.\n
            - `password`: This field is required.\n
            - `password2`: This field is required.\n
        """
        password_match_serializer = PasswordCheckMatchSerializer(
            data=request.data)

        if password_match_serializer.is_valid():
            if password_match_serializer.validated_data['password'] == password_match_serializer.validated_data['password2']:
                return Response({'match': True}, status=status.HTTP_200_OK)
            return Response({'match': False}, status=status.HTTP_200_OK)
        else:
            return Response(password_match_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated,]
    serializer_class = PasswordChangeSerializer
    lookup_field = 'username'

    def post(self, request: Request):
        """
        Change the password for the authenticated user.\n

        Finalize the password change process by providing the old and new passwords.\n
        The request must include the old password, new password, and confirmation of the new password.\n\n

        ### Request:\n
        - `old_password` (str): The current password of the user.\n
        - `new_password` (str): The new password for the user.\n
        - `confirm_new_password` (str): Confirmation of the new password.\n\n

        ### Response (Success):\n
        - `200 OK`:
        Password changed successfully.\n
            - `detail` (str): Password changed successfully.\n\n

        ### Response (Failure):\n
        - `400 Bad Request`:
        If the request data is invalid.\n
        - `401 Unauthorized`:
        If the provided current password is incorrect.
        """
        user_serializer = PasswordChangeSerializer(
            instance=request.user, data=request.data, partial=True)

        if user_serializer.is_valid():
            user_serializer.save()

            return Response({'detail': 'Password changed successfully.'}, status=status.HTTP_202_ACCEPTED)
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordRecoveryViewSet(viewsets.ViewSet):
    serializer_class = PasswordRecoveryRequestSerializer
    confirm_serializer_class = PasswordRecoveryConfirmSerializer

    def create(self, request):
        """
        Request a password reset link.\n

        Initiate the process to reset the user's password by sending a reset link to their email address.\n
        The request must include the user's email.\n\n

        ### Request:\n
        - `email` (str): The email address associated with the user's account.\n\n

        ### Response (Success):\n
        - `200 OK`:
        Password reset link sent successfully.\n
            - `detail` (str): Password reset link sent to the provided email address.\n\n

        ### Response (Failure):\n
        - `400 Bad Request`:
        If the request data is invalid.\n
        - `404 Not Found`:
        If no user is associated with the provided email.\n

        """
        serializer = PasswordRecoveryRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.filter(email=email).first()

            if user is not None:
                token = account_activation_token.make_token(user)
                expiration_time = timezone.now() + timedelta(minutes=90)

                ResetLink.objects.create(
                    user=user, token=token, expiration_time=expiration_time)

                send_email.delay(
                    request_domain=get_current_site(request).domain,
                    request_secure=request.is_secure(),
                    username=user.username,
                    to_email=email,
                    mail_subject="Welcome to Library Management System - Confirm sing up.",
                    template='email_confirmation_message.html',
                    token=token
                )

            return Response(
                {'detail': f'Password reset link sent to {email}, if the email is linked to an account.'},
                status=status.HTTP_200_OK
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        operation_id="password_recovery_create_with_uid_and_token",
        request=PasswordRecoveryConfirmSerializer,
        parameters=[
            OpenApiParameter("uidb64", str, OpenApiParameter.PATH),
            OpenApiParameter("token", str, OpenApiParameter.PATH)
        ]
    )
    @action(
        methods=['POST'], detail=False,
        url_path=r"(?P<uidb64>[^/.]+)/(?P<token>[^/.]+)",
        url_name="confirm"
    )
    def confirm_recovery(self, request, uidb64, token):
        """
        Confirm a password recovery request.\n

        Finalize the password recovery process by confirming the reset link.\n
        The request must include the user's UIDB64 and the token received in the reset link.\n\n

        ### Path Parameters:\n
        - `uidb64` (str): User ID encoded in base64.\n
        - `token` (str): Token received in the password recovery reset link.\n\n

        ### Request:\n
            - `new_password` (str): The new password for the user.\n
            - `confirm_new_password` (str): Confirmation of the new password.\n\n

        ### Response (Success):\n
        - `200 OK`:
        Password reset successfully confirmed.\n
            - `detail` (str): Password reset successfully.\n\n

        ### Response (Failure):\n
        - `400 Bad Request`:
        If the request data is invalid.\n
        - `400 Bad Request`:
        If the reset link is invalid.\n
        - `401 Unauthorized`:
        If the reset link has already been used or has expired.\n
        - `404 Not Found`:
        If no user is associated with the provided UIDB64.\n

        """
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            reset_link = ResetLink.objects.get(
                user=user, token=token, used=False)
        except:
            user = None
            reset_link = None

        serializer = self.confirm_serializer_class(data=request.data)

        if serializer.is_valid():
            if user is not None and account_activation_token.check_token(user, token):
                if reset_link != None and reset_link.is_valid():
                    new_password = serializer.validated_data['new_password']
                    user.set_password(new_password)
                    user.save()
                    reset_link.used = True
                    reset_link.save()
                    return Response({'detail': 'Password reset successfully.'}, status=status.HTTP_200_OK)
                else:
                    return Response({'detail': 'This link has already been used or has expired, request a new one.'}, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response({'detail': 'Invalid reset link.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailConfirmationView(APIView):
    serializer_class = DummySerializer

    @extend_schema(parameters=[
        OpenApiParameter("uidb64", str, OpenApiParameter.PATH),
        OpenApiParameter("token", str, OpenApiParameter.PATH)
    ])
    def get(self, request, uidb64, token):
        """
        Activate a user account using the provided UID and token.\n

        This endpoint is used to activate a user account by confirming the provided UID and token.\n

        ### Path Parameters:\n
        - `uidb64` (str): The base64-encoded user ID.\n
        - `token` (str): The activation token.\n\n

        ### Response (Success):\n
        - `200 OK`:
        Account activated successfully.\n
            - `detail` (str): Message indicating successful account activation.\n\n

        ### Response (Failure):\n
        - `400 BAD REQUEST`:
        Activation link is invalid.\n
            - `detail` (str): Message indicating that the activation link is invalid.\n

        """
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)

        except (TypeError, ValueError, OverflowError):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True

            user.save()

            return Response({'detail': 'Account activated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Activation link is invalid'}, status=status.HTTP_400_BAD_REQUEST)
