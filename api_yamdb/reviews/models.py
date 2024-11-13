from datetime import datetime

from django.core.validators import MaxValueValidator, validate_slug
from django.db import models


class Title(models.Model):
    name = models.CharField(max_length=256)
    year = models.IntegerField(
        validators=[MaxValueValidator(datetime.now().year)]
    )
    description = models.TextField(blank=True)
    genre = models.ManyToManyField('Genre')
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True
    )
    rating = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=256)
    slug = models.SlugField(
        unique=True, max_length=50, validators=[validate_slug]
    )

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=256)
    slug = models.SlugField(
        unique=True, max_length=50, validators=[validate_slug]
    )

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name
