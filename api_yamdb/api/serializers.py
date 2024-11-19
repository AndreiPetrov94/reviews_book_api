from django.utils.translation import gettext_lazy as _
import re

from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404

from rest_framework import serializers
from django.core import validators
# from rest_framework.exceptions import ValidationError
# from rest_framework.generics import get_object_or_404
# from rest_framework.validators import UniqueValidator

from reviews.constants import (
    MAX_LENGTH_EMAILFIELD,
    MAX_LENGTH_CHARFIELD_EMAIL_NAME
)
from reviews.models import Comment, Category, Genre, Title, Review, User


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username',
                  'bio', 'email', 'role']


class UserCreationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    username = serializers.CharField(required=True)

    def validate(self, data):
        username = data.get('username')

        # Проверка на запрещенное имя "me"
        if username and username.lower() == "me":
            raise serializers.ValidationError(
                {'username': _('Имя пользователя не может быть "me"')})

        # Проверка на допустимые символы в username
        if not re.match(r'^[\w.@+-]+$', username):
            raise serializers.ValidationError({
                'username': _('Имя пользователя может содержать только буквы, цифры и символы @/./+/-/_')
            })

        return data


class UserAccessTokenSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    confirmation_code = serializers.CharField(required=True)

    def validate(self, data):
        user = get_object_or_404(User, username=data['username'])
        if not default_token_generator.check_token(user,
                                                   data['confirmation_code']):
            raise serializers.ValidationError(
                {'confirmation_code': 'Неверный код подтверждения'})
        return data


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


class TitleReadSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(many=True, read_only=True)
    rating = serializers.IntegerField(read_only=True)

    # def to_representation(self, instance):
    #     repr = super().to_representation(instance)
    #     repr['category'] = CategorySerializer(instance.category).data
    #     repr['genre'] = GenreSerializer(instance.genre, many=True).data
    #     return repr

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'rating', 'description', 'genre', 'category')


class TitleCreateSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all()
    )
    genre = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Genre.objects.all(),
        many=True
    )

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'description', 'genre', 'category')


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
