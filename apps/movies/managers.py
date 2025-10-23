from django.db import models
from django.db.models import Avg, Count, Q


class MovieQuerySet(models.QuerySet):
    def with_ratings(self):
        return self.annotate(
            avg_rating=Avg('ratings__score'),
            ratings_count=Count('ratings', distinct=True),
            comments_count=Count('comments', distinct=True)
        )

    def by_category(self, category_slug: str):
        return self.filter(category__slug=category_slug)

    def by_year(self, year: int):
        return self.filter(year=year)

    def search(self, query: str):
        return self.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(director__icontains=query) |
            Q(actors__icontains=query)
        )

    def popular(self):
        return self.order_by('-views_count')

    def top_rated(self):
        return self.with_ratings().order_by('-avg_rating')

    def recent(self):
        return self.order_by('-created_at')


class MovieManager(models.Manager):
    def get_queryset(self):
        return MovieQuerySet(self.model, using=self._db)

    def with_ratings(self):
        return self.get_queryset().with_ratings()

    def by_category(self, category_slug: str):
        return self.get_queryset().by_category(category_slug)

    def search(self, query: str):
        return self.get_queryset().search(query)

    def popular(self):
        return self.get_queryset().popular()

    def top_rated(self):
        return self.get_queryset().top_rated()

    def recent(self):
        return self.get_queryset().recent()
