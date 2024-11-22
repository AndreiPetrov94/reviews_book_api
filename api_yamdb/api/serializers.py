from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from reviews.constants import (
    MAX_LENGTH_EMAILFIELD,
    MAX_LENGTH_CHARFIELD_NAME,
    MIN_VALUE_SCORE,
    MAX_VALUE_SCORE
)
from reviews.models import Comment, Category, Genre, Title, Review, User
from reviews.validators import validation_username


class BaseUserSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=MAX_LENGTH_CHARFIELD_NAME,
        required=True
    )

    def validate_username(self, value):
        return validation_username(value)


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'first_name', 'last_name',
            'username', 'bio',
            'email', 'role'
        )


# class UserCreationSerializer(BaseUserSerializer):
#     email = serializers.EmailField(
#         max_length=MAX_LENGTH_EMAILFIELD,
#         required=True
#     )

#     def validate(self, attrs):
#         user_by_email = User.objects.filter(email=attrs.get('email')).first()
#         user_by_username = User.objects.filter(
#             username=attrs.get('username')
#         ).first()

#         if user_by_email and user_by_email.username != attrs.get('username'):
#             raise serializers.ValidationError(
#                 {'email': 'Электронная почта уже используется'}
#             )

#         if user_by_username and user_by_username.email != attrs.get('email'):
#             raise serializers.ValidationError(
#                 {'username': 'Никнейм уже используется'}
#             )
#         return super().validate(attrs)

#     def create(self, validated_data):
#         user = User.objects.create(
#             email=validated_data['email'],
#             username=validated_data['username']
#         )
#         confirmation_code = user.generate_confirmation_code()
#         user.confirmation_code = confirmation_code
#         user.save()
#         send_mail(
#             f'Ваш код подтверждения {confirmation_code}',
#             settings.DEFAULT_FROM_EMAIL,
#             [validated_data['email']],
#             fail_silently=False
#         )
#         return user


class UserEditSerializer(BaseUserSerializer, serializers.ModelSerializer):

    def validate_username(self, value):
        return validation_username(value)

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


class SignupSerializer(BaseUserSerializer):
    email = serializers.EmailField(
        max_length=MAX_LENGTH_EMAILFIELD,
        required=True
    )

    def validate(self, data):
        email = data.get('email')
        username = data.get('username')
        if User.objects.filter(email=email).exclude(
            username=username
        ).exists():
            raise serializers.ValidationError(
                {'email': 'Электронная почта уже используется'}
            )
        if User.objects.filter(username=username).exclude(
            email=email
        ).exists():
            raise serializers.ValidationError(
                {'username': 'Никнейм уже используется'}
            )
        return data

    def create(self, validated_data):
        user, created = User.objects.get_or_create(
            username=validated_data['username'],
            email=validated_data['email']
        )
        confirmation_code = default_token_generator.make_token(user)
        user.confirmation_code = confirmation_code
        user.save()
        email_body = (
            f'Доброго времени суток, {user.username}. '
            f'Код подтверждения для доступа к API: {confirmation_code}'
        )
        send_mail(
            subject='Код подтверждения для доступа к API!',
            message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return user


class TokenSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    confirmation_code = serializers.CharField(required=True)
    token = serializers.CharField(read_only=True)

    def validate(self, data):
        username = data.get('username')
        confirmation_code = data.get('confirmation_code')
        user = get_object_or_404(User, username=username)
        if not default_token_generator.check_token(user, confirmation_code):
            raise serializers.ValidationError(
                {'confirmation_code': 'Неверный код подтверждения'}
            )
        data['token'] = str(RefreshToken.for_user(user).access_token)
        return data


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
