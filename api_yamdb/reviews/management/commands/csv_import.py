# import csv
# from pathlib import Path

# from django.core.management.base import BaseCommand

# from reviews.models import Category, Comment, Genre, Title, Review, User


# class Command(BaseCommand):

#     def handle(self, *args, **options):
#         path = Path('./static/data')
#         for file in path.iterdir():
#             with open(file, encoding='utf-8') as f:
#                 reader = csv.DictReader(f)
#                 for row in reader:
#                     if file.name == 'category.csv':
#                         Category.objects.create(**row)
#                     elif file.name == 'genre.csv':
#                         Genre.objects.create(**row)
#                     elif file.name == 'users.csv':
#                         User.objects.create(**row)
#                     elif file.name == 'titles.csv':
#                         Title.objects.create(**row)
#                     elif file.name == 'review.csv':
#                         Review.objects.create(**row)
#                     elif file.name == 'comments.csv':
#                         Comment.objects.create(**row)

#         self.stdout.write(self.style.SUCCESS('Данные импортированы'))
