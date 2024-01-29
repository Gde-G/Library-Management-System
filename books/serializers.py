from datetime import date

from rest_framework import serializers

from .models import Author, Genre, Publisher, Book


class BaseAuthorSerializer (serializers.ModelSerializer):
    class Meta:
        model = Author
        exclude = ['created_at', 'updated_at']


class ListAuthorSerializer (BaseAuthorSerializer):

    def to_representation(self, instance):
        data = {
            'id': instance.id,
            'name': f'{instance.first_name.capitalize()} {instance.last_name.capitalize()}',
            'biography': instance.biography,
            'picture': instance.picture.url,
            'nationality': instance.nationality,
            'birth_date': instance.birth_date,
            'death_date': instance.death_date,
        }
        return data


class CreateAuthorSerializer (BaseAuthorSerializer):

    def to_internal_value(self, data):
        data['first_name'] = data['first_name'].lower()
        data['last_name'] = data['last_name'].lower()

        return super().to_internal_value(data)

    def validate(self, data):
        birth_date = data['birth_date']
        try:
            death_date = data['death_date']

            if death_date and death_date < birth_date:
                raise serializers.ValidationError(
                    {"death_date": "Death date must be on or after the birth date."}
                )
        except KeyError:
            pass

        if birth_date > date.today():
            raise serializers.ValidationError(
                {"birth_date": "Birth date must be in the past."}
            )
        return super().validate(data)


class UpdateAuthorSerializer(BaseAuthorSerializer):

    def to_internal_value(self, data):
        data_new = {}
        data_new['first_name'] = data['first_name'].lower()
        data_new['last_name'] = data['last_name'].lower()

        return super().to_internal_value(data_new)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


class BaseGenreSerializer(serializers.ModelSerializer):

    class Meta:
        model = Genre
        exclude = ['id']


class GenericGenreSerializer(BaseGenreSerializer):

    class Meta:
        model = Genre
        exclude = ['id', 'slug']


class BasePublisherSerializer(serializers.ModelSerializer):

    class Meta:
        model = Publisher
        fields = '__all__'


class GenericPublisherSerializer(serializers.ModelSerializer):

    class Meta:
        model = Publisher
        exclude = ['id']


class BaseBookSerializer(serializers.ModelSerializer):

    class Meta:
        model = Book
        fields = [
            'title', 'author', 'language', 'genre', 'publisher',
            'edition', 'amount_pages', 'cover', 'publication_date',
            'slug'
        ]


class CreateBookSerializer(BaseBookSerializer):
    genre = serializers.PrimaryKeyRelatedField(
        queryset=Genre.objects.all(), allow_null=False, required=True)
    author = serializers.PrimaryKeyRelatedField(
        queryset=Author.objects.all(), allow_null=False, required=True)
    publisher = serializers.PrimaryKeyRelatedField(
        queryset=Publisher.objects.all(), allow_null=True, required=False)

    class Meta(BaseBookSerializer.Meta):
        fields = BaseBookSerializer.Meta.fields.copy()
        fields.remove('slug')

    def validate_publication_date(self, value):
        if value is None:
            raise serializers.ValidationError(
                {'publication_date': 'This field is required.'}
            )

        if value > date.today():
            raise serializers.ValidationError(
                {'publication_date': 'Publication date must be on or before today.'}
            )

        return value


class ListBookSerializer(BaseBookSerializer):
    author = ListAuthorSerializer(read_only=True, required=False)
    genre = BaseGenreSerializer(read_only=True)
    publisher = BasePublisherSerializer(read_only=True, required=False)

    def to_representation(self, instance):
        base_representation = super().to_representation(instance)

        author_representation = self.fields['author'].to_representation(
            instance.author)if instance.author else None
        genre_representation = self.fields['genre'].to_representation(
            instance.genre)

        publisher_representation = self.fields['publisher'].to_representation(
            instance.publisher) if instance.publisher else None

        base_representation['author'] = author_representation
        base_representation['genre'] = genre_representation
        base_representation['publisher'] = publisher_representation

        return base_representation


class UpdateBookSerializer(CreateBookSerializer):

    def validate_amount_pages(self, value):

        if value <= 0:
            raise serializers.ValidationError(
                {'amount_pages': 'Amount of pages must be a positive integer.'})

        return value

    def update(self, instance: Book, validated_data):

        instance.title = validated_data.get('title', instance.title)
        instance.author = validated_data.get('author', instance.author)
        instance.language = validated_data.get('language', instance.language)
        instance.genre = validated_data.get('genre', instance.genre)
        instance.publisher = validated_data.get(
            'publisher', instance.publisher)
        instance.edition = validated_data.get('edition', instance.edition)
        instance.amount_pages = validated_data.get(
            'amount_pages', instance.amount_pages)
        instance.cover = validated_data.get('cover', instance.cover)
        instance.publication_date = validated_data.get(
            'publication_date', instance.publication_date)

        instance.save()

        return instance
