from django.contrib.auth.tokens import default_token_generator
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from reviews.constants import (
    MAX_LENGTH_EMAILFIELD,
    MAX_LENGTH_CHARFIELD_NAME,
    MIN_VALUE_SCORE,
    MAX_VALUE_SCORE
)
from reviews.models import Comment, Category, Genre, Title, Review, User
from reviews.validators import validation_username


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
        if value.lower() == 'me':
            raise serializers.ValidationError(
                'Никнейм не может быть "me"'
            )
        validation_username(value)
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
        username = data.get('username')
        confirmation_code = data.get('confirmation_code')
        user = get_object_or_404(
            User,
            username=username
        )
        if user.confirmation_code != confirmation_code:
            return Response(
                {'Неверный код подтверждения'},
                status=status.HTTP_400_BAD_REQUEST
            )
        token = AccessToken.for_user(user)
        return Response({'token': str(token)}, status=status.HTTP_201_CREATED)


class SignupSerializer(BaseUserSerializer):
    email = serializers.EmailField(
        max_length=MAX_LENGTH_EMAILFIELD,
        required=True
    )

    def validate(self, attrs):
        email = attrs.get('email')
        username = attrs.get('username')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        if user is not None and user.username != username:
            raise serializers.ValidationError(
                {'email': 'Электронная почта уже используется'}
            )

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user is not None and user.email != email:
            raise serializers.ValidationError(
                {'username': 'Никнейм уже используется'}
            )

        return attrs

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
        if MIN_VALUE_SCORE > value > MAX_VALUE_SCORE:
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
