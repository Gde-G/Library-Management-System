from datetime import date
from decimal import Decimal

from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from books.models import Book
from books.serializers import ListBookSerializer
from .models import Favorite, Reservation, Credit, Strike, Penalty, StrikeGroup, Notification
from .utils import calculate_penalty_price


class CreateFavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = ['book']

    def validation_book(self, value):
        book = Book.objects.filter(slug=value)

        if not book.exists():
            raise serializers.ValidationError(
                {'book': 'Book not exists.'}
            )
        return book


class ListFavoriteSerializer(ListBookSerializer):

    pass


class BaseReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = [
            'id', 'start_date', 'end_date', 'initial_price',
            'status', 'returned_date', 'penalty_price', 'final_price',
            'notes', 'created_at', 'book'
        ]


class CreateReservationSerializer(BaseReservationSerializer):
    class Meta(BaseReservationSerializer.Meta):
        fields = ['book', 'start_date', 'end_date', 'notes']

    def validate_start_date(self, value):
        if value < date.today():
            raise serializers.ValidationError(
                {'start_date': 'Must be a future date.'}
            )
        return value

    def validate(self, attrs):
        start_date = attrs.get('start_date', None)
        end_date = attrs.get('end_date', None)
        book = attrs.get('book', None)

        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError(
                {'end_date': 'Must be after the start_date.'}
            )

        # Check availability of the book on this period
        overlapping_reservations = Reservation.objects.filter(
            Q(book=book) &
            Q(start_date__lte=end_date) &
            Q(end_date__gte=start_date)
        )

        if overlapping_reservations.exists():
            raise serializers.ValidationError(
                {'book': 'This book is not available for the specified period.'}
            )

        return super().validate(attrs)


class ListReservationSerializer(BaseReservationSerializer):
    book = ListBookSerializer(read_only=True)

    def to_representation(self, instance):
        base_representation = super().to_representation(instance)

        book_representation = self.fields['book'].to_representation(
            instance.book)
        base_representation['book'] = book_representation

        return base_representation


class PatchReservationSerializer(BaseReservationSerializer):
    retired = serializers.BooleanField(required=False)

    class Meta(BaseReservationSerializer.Meta):
        fields = ['returned_date', 'retired']

    def update(self, instance: Reservation, validated_data):
        returned_date = validated_data.get('returned_date', None)
        retired = validated_data.get('retired', None)
        if returned_date and retired:
            raise serializers.ValidationError(
                {'returned_date_and_retired': 'Can not process retired and returned_date at once. Choose only one.'}
            )
        elif returned_date:
            instance.returned_date = returned_date
            penalty_price = calculate_penalty_price(
                instance.end_date,
                initial_price=instance.initial_price,
                returned_date=returned_date
            )
            if penalty_price is not None:
                instance.penalty_price = Decimal(penalty_price)
            else:
                raise serializers.ValidationError(
                    {'penalty_price': 'Error calculating penalty price.'}
                )

            instance.final_price = instance.penalty_price + instance.initial_price
            instance.status = 'completed'

            instance.save()

        elif retired:
            if instance.end_date > date.today():
                instance.status = 'retired'
                instance.save()
            else:
                raise serializers.ValidationError(
                    {'retired': 'Impossible to retire book, reservation period end.'}
                )
        else:
            raise serializers.ValidationError(
                {'non_fields': 'Is required parse one of the two possible fields.'}
            )

        return instance


class CheckReservationAvailabilitySerializer(serializers.Serializer):
    book = serializers.SlugField(required=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)

    def validate_start_date(self, value):
        if value and value < date.today():
            raise serializers.ValidationError(
                {'start_date': 'Must be a future date.'}
            )
        return value

    def validate(self, attrs):
        book = attrs.get('book')
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')

        book = Book.objects.filter(slug=book).first()

        if not book:
            raise serializers.ValidationError(
                {'book': 'Book not found.'}
            )

        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError(
                {'end_date': 'Must be after the start_date.'}
            )

        return attrs


class UnavailableReservationPeriodsSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)


class CreditRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Credit
        exclude = ['id']


class CreditPatchSerializer(serializers.ModelSerializer):
    subtract = serializers.IntegerField()

    class Meta:
        model = Credit
        fields = ['subtract']

    def validate_subtract(self, value):
        if type(value) == int or value.isdigit():
            value = int(value)
            if value <= 0:
                raise serializers.ValidationError(
                    {'subtract': 'Must be bigger than 0.'}
                )
        else:
            raise serializers.ValidationError(
                {'subtract': 'Must be an integer.'}
            )

        return value

    def update(self, instance: Credit, validated_data):

        if instance.amount < validated_data['subtract']:
            raise serializers.ValidationError(
                {'subtract': 'Not have enough credits to make the change.'}
            )

        instance.amount -= validated_data['subtract']
        instance.save()

        return instance


class StrikeListSerializer(serializers.ModelSerializer):
    reservation = ListReservationSerializer(read_only=True)

    class Meta:
        model = Strike
        fields = ['reason', 'reservation']


class PenaltyListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Penalty
        fields = '__all__'


class PenaltyRetrieveSerializer(serializers.ModelSerializer):
    penalty = PenaltyListSerializer(read_only=True)
    strikes = StrikeListSerializer(read_only=True, many=True)

    class Meta:
        model = StrikeGroup
        fields = ['penalty', 'strikes']


class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = ['model']


class NotificationSerializer(serializers.ModelSerializer):
    content_type = ContentTypeSerializer()
    content_object = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'is_read',
                  'created_at', 'content_type', 'content_object']

    @extend_schema_field(serializers.DictField,)
    def get_content_object(self, obj):
        model_name = obj.content_type.model
        if model_name == 'reservation':
            serializer = ListReservationSerializer(obj.content_object)
        elif model_name == 'credit':
            serializer = CreditRetrieveSerializer(obj.content_object)
        elif model_name == 'strike':
            serializer = StrikeListSerializer(obj.content_object)
        elif model_name == 'penalty':
            serializer = PenaltyListSerializer(obj.content_object)

        return serializer.data

    def to_representation(self, instance):

        base_representation = super().to_representation(instance)
        content_type = base_representation.pop('content_type')
        content_object = base_representation.pop('content_object')
        base_representation['type'] = content_type['model']
        base_representation[f"{content_type['model']}"] = content_object

        return base_representation
