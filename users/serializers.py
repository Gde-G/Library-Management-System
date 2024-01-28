from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core import exceptions as django_exceptions
from django.db import IntegrityError, transaction
from rest_framework import serializers
from rest_framework.settings import api_settings
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


from .models import User


class ListProfileUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'username',  'email',
            'first_name', 'last_name', 'birth_date',
            'profile_img', 'create_at',
        ]

    def to_representation(self, instance):
        try:
            return {
                'username': instance['username'],
                'email': instance['email'],
                'first_name': instance['first_name'],
                'last_name': instance['last_name'],
                'birth_date': instance['birth_date'],
                'profile_img': instance.profile_img.url if instance['profile_img'] else '',
                'create_at': _(instance['create_at'].strftime("%B of %Y")),
            }
        except:
            return {
                'username': instance.username,
                'email': instance.email,
                'first_name': instance.first_name,
                'last_name': instance.last_name,
                'birth_date': instance.birth_date,
                'profile_img': instance.profile_img.url if instance.profile_img else '',
                'create_at': _(instance.create_at.strftime("%B of %Y")),
            }


class ListSimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'username', 'profile_img'
        ]

    def to_representation(self, instance):

        try:
            return {
                'username': instance['username'],
                'profile_img': instance.profile_img.url if instance['profile_img'] else '',
            }
        except:
            return {
                'username': instance.username,
                'profile_img': instance.profile_img.url if instance.profile_img else '',
            }


class CreateUserSerializer(serializers.ModelSerializer):

    password2 = serializers.CharField(required=True)

    class Meta:
        model = User

        exclude = [
            'groups', 'user_permissions',
            'is_active', 'is_staff', 'is_superuser', 'last_login'
        ]

    def validate_user_handle(self, user_handle):
        """
        Custom validation to ensure case-insensitive user_handle uniqueness.
        """
        User = self.Meta.model
        if User.objects.filter(user_handle__iexact=user_handle).exists():
            raise serializers.ValidationError(
                "This user_handle is already in use.")
        return user_handle

    def validate(self, data):
        if data.get('password') != data.get('password2'):
            raise serializers.ValidationError(
                {"password": "Passwords do not match."})

        data.pop('password2')

        return data

    def create(self, validated_data):
        validated_data['username'] = validated_data['username'].lower()
        user = self.Meta.model(**validated_data)
        user.set_password(validated_data['password'])

        user.save()
        return user


class UpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User

        exclude = [
            'password', 'create_at', 'groups', 'user_permissions',
            'is_active', 'is_staff', 'is_superuser', 'last_login'
        ]

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    pass


class SetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(
        max_length=252, min_length=8, write_only=True)
    password2 = serializers.CharField(
        max_length=252, min_length=8, write_only=True)

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError(
                {'password2': "Passwords do not match"})

        return data['password']


class PasswordCheckMatchSerializer(serializers.Serializer):
    password = serializers.CharField()
    password2 = serializers.CharField()

    def validate(self, data):
        keys = data.keys()
        if 'password' not in keys:
            raise serializers.ValidationError(
                {'password': 'This field is required.'})
        elif 'password2' not in keys:
            raise serializers.ValidationError(
                {'password2': 'This field is required.'})
        else:
            return data


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_new_password = serializers.CharField(
        required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError(
                {'confirm_new_password': 'Passwords not match.'}
            )

        return super().validate(attrs)

    def update(self, instance: User, validated_data):
        if not instance.check_password(validated_data['old_password']):
            raise serializers.ValidationError({
                'old_password': 'Wrong password.'
            })

        try:
            validate_password(validated_data['new_password'])
        except ValidationError as e:

            raise serializers.ValidationError({'new_password': str(e)})

        instance.set_password(validated_data['new_password'])
        instance.save()

        return instance


class PasswordRecoveryRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class PasswordRecoveryConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_new_password = serializers.CharField(
        required=True, write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError(
                {'confirm_new_password': "Passwords do not match"})

        return data
