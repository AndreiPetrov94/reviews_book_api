from rest_framework import serializers
from django.core import validators
# from rest_framework.exceptions import ValidationError
# from rest_framework.generics import get_object_or_404
from rest_framework.validators import UniqueValidator

from reviews.constants import (
    MAX_LENGTH_EMAILFIELD,
    MAX_LENGTH_CHARFIELD_EMAIL_NAME
)
from reviews.models import Comment, Category, Genre, Title, Review, User


class UserSerializer(serializers.ModelSerializer):
    username = serializers.SlugField(
        max_length=MAX_LENGTH_CHARFIELD_EMAIL_NAME,
        validators=(
            validators.MaxLengthValidator(MAX_LENGTH_CHARFIELD_EMAIL_NAME),
            validators.RegexValidator(r'^[\w.@+-]+\Z')
        )
    )
    email = serializers.EmailField(
        max_length=MAX_LENGTH_EMAILFIELD,
        validators=(validators.MaxLengthValidator(MAX_LENGTH_EMAILFIELD),)
    )

    def validate(self, attrs):
        if User.objects.filter(email=attrs.get('email')).exists():
            user = User.objects.get(email=attrs.get('email'))
            if user.username != attrs.get('username'):
                raise serializers.ValidationError(
                    'Электронная почта уже использована'
                )
        if User.objects.filter(username=attrs.get('username')).exists():
            user = User.objects.get(username=attrs.get('username'))
            if user.email != attrs.get('email'):
                raise serializers.ValidationError(
                    'Имя пользователя уже использовано'
                )
        return super().validate(attrs)

    def validate_username(self, value):
        if value == "me":
            raise serializers.ValidationError(
                'Имя пользователя не может быть "me"'
            )
        return value

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'role'
        )
        lookup_field = 'username'
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
        }


class UserEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'role'
        )
        read_only_fields = ('role')


class SignupSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        max_length=MAX_LENGTH_CHARFIELD_EMAIL_NAME,
        required=True
    )
    email = serializers.EmailField(
        max_length=MAX_LENGTH_EMAILFIELD,
        required=True
    )

    def validate_username(self, value):
        if value.lower() == "me":
            raise serializers.ValidationError(
                'Имя пользователя не может быть "me"'
            )
        return value

    class Meta:
        model = User
        fields = ('username', 'email')


class TokenSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    confirmation_code = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('username', 'confirmation_code')


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        model = Genre
        fields = ('name', 'slug')


class TitleSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all()
    )
    genre = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Genre.objects.all(),
        many=True
    )

    def to_representation(self, instance):
        repr = super().to_representation(instance)
        repr['category'] = CategorySerializer(instance.category).data
        repr['genre'] = GenreSerializer(instance.genre, many=True).data
        return repr

    class Meta:
        model = Title
        fields = ('name', 'year', 'description', 'genre', 'category', 'rating')


class ReviewSerializer(serializers.ModelSerializer):
    title = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True,
    )
    author = serializers.SlugRelatedField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
        read_only=True
    )

    def validate_score(self, value):
        if 0 > value > 10:
            raise serializers.ValidationError(
                'Оценка по 10-бальной шкале!'
            )
        return value

    def validate(self, data):
        if self.context['request'].method == 'POST':
            if Review.objects.filter(
                author=self.context['request'].user,
                title=self.context['view'].kwargs.get('title_id')
            ).exists():
                raise serializers.ValidationError(
                    'Одно произведение - один отзыв!'
                )
        return data

    class Meta:
        model = Review
        fields = ('text', 'author', 'title', 'score', 'pub_date')


class CommentSerializer(serializers.ModelSerializer):
    review = serializers.SlugRelatedField(
        slug_field='text',
        read_only=True
    )
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Comment
        fields = ('text', 'author', 'review', 'pub_date')
