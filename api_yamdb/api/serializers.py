from rest_framework import serializers

from reviews.models import Category, Genre, Title


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
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        model = Genre
        fields = ('name', 'slug')
