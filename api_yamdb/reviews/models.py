from datetime import datetime

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.tokens import default_token_generator
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    validate_slug)
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from reviews.constants import (
    MAX_LENGTH_CHARFIELD,
    MAX_LENGTH_EMAILFIELD,
    MAX_LENGTH_SLUGFIELD,
    MAX_LENGTH_TEXTFIELD,
    MAX_LENGTH_CHARFIELD_CODE,
    MAX_LENGTH_CHARFIELD_NAME,
    MAX_LENGTH_CHARFIELD_ROLE,
    MIN_VALUE_SCORE,
    MAX_VALUE_SCORE
)
from reviews.validators import validation_username


class User(AbstractUser):
    ADMIN = 'admin'
    MODERATOR = 'moderator'
    USER = 'user'
    ROLES = (
        (ADMIN, ADMIN),
        (MODERATOR, MODERATOR),
        (USER, USER)
    )
    username = models.CharField(
        verbose_name='Никнейм',
        max_length=MAX_LENGTH_CHARFIELD_NAME,
        blank=False,
        null=False,
        unique=True,
        validators=(validation_username,)
    )
    email = models.EmailField(
        verbose_name='Электронная почта',
        max_length=MAX_LENGTH_EMAILFIELD,
        blank=False,
        null=False,
        unique=True
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=MAX_LENGTH_CHARFIELD_NAME,
        blank=True
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=MAX_LENGTH_CHARFIELD_NAME,
        blank=True
    )
    bio = models.TextField(
        verbose_name='Биография',
        max_length=MAX_LENGTH_TEXTFIELD,
        blank=True
    )
    role = models.CharField(
        verbose_name='Роль',
        max_length=MAX_LENGTH_CHARFIELD_ROLE,
        choices=ROLES,
        default=USER,
        blank=True
    )
    confirmation_code = models.CharField(
        verbose_name='Код потверждения',
        max_length=MAX_LENGTH_CHARFIELD_CODE,
        blank=True,
        null=True,
        default='XXXX'
    )

    @property
    def is_admin(self):
        return self.role == User.ADMIN or self.is_superuser

    @property
    def is_moderator(self):
        return self.role == User.MODERATOR

    @property
    def is_user(self):
        return self.role == User.USER

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

        constraints = [
            models.CheckConstraint(
                check=~models.Q(username__iexact='me'),
                name='username_is_not_me'
            )
        ]

    def __str__(self):
        return self.username


@receiver(post_save, sender=User)
def post_save(sender, instance, created, **kwargs):
    if created:
        confirmation_code = default_token_generator.make_token(
            instance
        )
        instance.confirmation_code = confirmation_code
        instance.save()


class Category(models.Model):
    name = models.CharField(
        verbose_name='Название категории',
        max_length=MAX_LENGTH_CHARFIELD
    )
    slug = models.SlugField(
        verbose_name='Слаг',
        max_length=MAX_LENGTH_SLUGFIELD,
        unique=True,
        validators=(validate_slug,)
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(
        verbose_name='Название жанра',
        max_length=MAX_LENGTH_CHARFIELD
    )
    slug = models.SlugField(
        verbose_name='Слаг',
        max_length=MAX_LENGTH_SLUGFIELD,
        unique=True,
        validators=(validate_slug,)
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return self.name


class Title(models.Model):
    name = models.CharField(
        verbose_name='Название произведения',
        max_length=MAX_LENGTH_CHARFIELD
    )
    year = models.IntegerField(
        verbose_name='Дата выхода',
        validators=[MaxValueValidator(datetime.now().year)]
    )
    description = models.TextField(
        verbose_name='Описание',
        blank=True,
        null=True
    )
    genre = models.ManyToManyField(
        Genre,
        verbose_name='Жанр',
        related_name='titles'
    )
    category = models.ForeignKey(
        Category,
        verbose_name='Категория',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='titles'
    )

    class Meta:
        ordering = ['-year']
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'

    def __str__(self):
        return self.name


class Review(models.Model):
    text = models.TextField(
        verbose_name='Текст отзыва',
        max_length=MAX_LENGTH_CHARFIELD,
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    title = models.ForeignKey(
        Title,
        verbose_name='Название произведения',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    score = models.IntegerField(
        verbose_name='Рейтинг',
        validators=[
            MinValueValidator(MIN_VALUE_SCORE, 'Оценка по 10-бальной шкале!'),
            MaxValueValidator(MAX_VALUE_SCORE, 'Оценка по 10-бальной шкале!')
        ]
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата отзыва',
        auto_now_add=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='unique_review'
            ),
        ]

    def __str__(self):
        return self.text


class Comment(models.Model):
    text = models.TextField(
        verbose_name='Текст комментария',
        max_length=MAX_LENGTH_CHARFIELD
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    review = models.ForeignKey(
        Review,
        verbose_name='Отзыв',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата комментария',
        auto_now_add=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text
