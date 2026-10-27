from datetime import timedelta

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Director(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True)
    photo_url = models.URLField(blank=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Movie(models.Model):
    AGE_RATINGS = [
        ("0+", "0+"),
        ("6+", "6+"),
        ("12+", "12+"),
        ("16+", "16+"),
        ("18+", "18+"),
    ]

    title = models.CharField(max_length=200)
    original_title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    director = models.ForeignKey(
        Director, on_delete=models.PROTECT, related_name="movies"
    )
    genres = models.ManyToManyField(Genre, related_name="movies", blank=True)
    duration_min = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(600)]
    )
    release_year = models.PositiveIntegerField(
        validators=[MinValueValidator(1888), MaxValueValidator(2100)]
    )
    country = models.CharField(max_length=100, blank=True)
    age_rating = models.CharField(max_length=3, choices=AGE_RATINGS)
    cast = models.TextField(blank=True)
    poster_url = models.URLField(blank=True)
    trailer_url = models.URLField(blank=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Hall(models.Model):
    name = models.CharField(max_length=100, unique=True)
    rows_count = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(50)]
    )
    seats_per_row = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(50)]
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Session(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.PROTECT, related_name="sessions")
    hall = models.ForeignKey(Hall, on_delete=models.PROTECT, related_name="sessions")
    start_time = models.DateTimeField()
    price = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(0)]
    )

    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        return f"{self.movie} — {self.hall} — {self.start_time:%Y-%m-%d %H:%M}"

    @property
    def end_time(self):
        return self.start_time + timedelta(minutes=self.movie.duration_min)
