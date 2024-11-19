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
    MAX_LENGTH_EMAILFIELD,
    MAX_LENGTH_CHARFIELD_EMAIL_NAME,
    MAX_LENGTH_CHARFIELD,
    MAX_LENGTH_SLUGFIELD
)
# from reviews.validators import validate_username


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
        # validators=(validate_username,),
        max_length=MAX_LENGTH_CHARFIELD_EMAIL_NAME,
        blank=False,
        null=False,
        unique=True
    )
    email = models.EmailField(
        max_length=MAX_LENGTH_EMAILFIELD,
        blank=False,
        null=False,
        unique=True
    )
    first_name = models.CharField(
        max_length=MAX_LENGTH_CHARFIELD_EMAIL_NAME,
        blank=True
    )
    last_name = models.CharField(
        max_length=MAX_LENGTH_CHARFIELD_EMAIL_NAME,
        blank=True
    )
    bio = models.TextField(
        blank=True
    )
    role = models.CharField(
        max_length=20,
        choices=ROLES,
        default=USER,
        blank=True
    )
    confirmation_code = models.CharField(
        max_length=255,
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
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

        constraints = [
            models.CheckConstraint(
                check=~models.Q(username__iexact="me"),
                name="username_is_not_me"
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
    name = models.CharField(max_length=MAX_LENGTH_CHARFIELD)
    slug = models.SlugField(
        max_length=MAX_LENGTH_SLUGFIELD,
        validators=[validate_slug],
        unique=True
    )

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=MAX_LENGTH_CHARFIELD)
    slug = models.SlugField(
        max_length=MAX_LENGTH_SLUGFIELD,
        validators=[validate_slug],
        unique=True
    )

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return self.name


class Title(models.Model):
    name = models.CharField(max_length=MAX_LENGTH_CHARFIELD)
    year = models.IntegerField(
        validators=[MaxValueValidator(datetime.now().year)]
    )
    description = models.TextField(
        blank=True,
        null=True
    )
    genre = models.ManyToManyField(
        Genre,
        related_name='titles'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name='titles',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'

    def __str__(self):
        return self.name


class Review(models.Model):
    text = models.TextField(max_length=MAX_LENGTH_CHARFIELD)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    score = models.IntegerField(
        validators=[
            MinValueValidator(1, 'Допустимы значения от 1 до 10'),
            MaxValueValidator(10, 'Допустимы значения от 1 до 10')
        ]
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    class Meta:
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
    text = models.TextField(max_length=MAX_LENGTH_CHARFIELD)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['pub_date']

    def __str__(self):
        return self.text
