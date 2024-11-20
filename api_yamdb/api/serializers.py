import re

from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from reviews.constants import (
    MAX_LENGTH_EMAILFIELD,
    MAX_LENGTH_CHARFIELD_NAME
)
from reviews.models import Comment, Category, Genre, Title, Review, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name',
            'username', 'bio',
            'email', 'role'
        )


class BaseUserSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=MAX_LENGTH_CHARFIELD_NAME,
        required=True
    )

    def validate_username(self, value):
        if value.lower() == "me":
            raise serializers.ValidationError(
                'Никнейм не может быть "me"'
            )
        if not re.match(r'^[\w.@+-]+\Z', value):
            raise serializers.ValidationError(
                'Недопустимые символы в никнейме'
            )
        return value


class UserCreationSerializer(BaseUserSerializer):
    email = serializers.EmailField(
        max_length=MAX_LENGTH_EMAILFIELD,
        required=True
    )

    def validate(self, data):
        data = super().validate(data)
        return data


class UserEditSerializer(BaseUserSerializer, serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'first_name', 'last_name',
            'username', 'bio',
            'email', 'role'
        )
        read_only_fields = ('role',)


class UserAccessTokenSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    confirmation_code = serializers.CharField(required=True)

    def validate(self, data):
        user = get_object_or_404(
            User,
            username=data['username']
        )
        if not default_token_generator.check_token(
            user,
            data['confirmation_code']
        ):
            raise serializers.ValidationError(
                {'Неверный код подтверждения'}
            )
        return data


class SignupSerializer(BaseUserSerializer, serializers.ModelSerializer):
    email = serializers.EmailField(
        max_length=MAX_LENGTH_EMAILFIELD,
        required=True
    )

    def validate(self, attrs):
        if User.objects.filter(email=attrs.get('email')).exists():
            user = User.objects.get(email=attrs.get('email'))
            if user.username != attrs.get('username'):
                raise serializers.ValidationError(
                    {'Электронная почта уже используется'}
                )
        if User.objects.filter(username=attrs.get('username')).exists():
            user = User.objects.get(username=attrs.get('username'))
            if user.email != attrs.get('email'):
                raise serializers.ValidationError(
                    {'Никнейм уже используется'}
                )
        return super().validate(attrs)

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

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'rating',
            'description', 'genre', 'category'
        )


class TitleCreateSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='slug',
    )
    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(),
        many=True,
        slug_field='slug'
    )

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year',
            'description', 'genre', 'category'
        )


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

    def validate_score(self, value):
        if 0 > value > 10:
            raise serializers.ValidationError(
                'Оценка по 10-бальной шкале!'
            )
        return value

    class Meta:
        model = Review
        fields = (
            'id', 'text', 'author',
            'title', 'score', 'pub_date'
        )


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
        fields = (
            'id', 'text', 'author',
            'review', 'pub_date'
        )
