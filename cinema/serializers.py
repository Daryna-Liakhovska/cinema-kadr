from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from .exceptions import ConflictError
from .models import Director, Genre, Hall, Movie, Session


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "name"]


class DirectorShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Director
        fields = ["id", "first_name", "last_name"]


class DirectorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Director
        fields = ["id", "first_name", "last_name", "photo_url"]


class DirectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Director
        fields = [
            "id",
            "first_name",
            "last_name",
            "bio",
            "birth_date",
            "country",
            "photo_url",
        ]


class MovieListSerializer(serializers.ModelSerializer):
    director = DirectorShortSerializer(read_only=True)
    genres = GenreSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = [
            "id",
            "title",
            "poster_url",
            "release_year",
            "duration_min",
            "age_rating",
            "genres",
            "director",
        ]


class MovieSerializer(serializers.ModelSerializer):
    director = DirectorShortSerializer(read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    director_id = serializers.PrimaryKeyRelatedField(
        queryset=Director.objects.all(), source="director", write_only=True
    )
    genre_ids = serializers.PrimaryKeyRelatedField(
        queryset=Genre.objects.all(),
        source="genres",
        many=True,
        write_only=True,
        required=False,
    )

    class Meta:
        model = Movie
        fields = [
            "id",
            "title",
            "original_title",
            "description",
            "director",
            "director_id",
            "genres",
            "genre_ids",
            "duration_min",
            "release_year",
            "country",
            "age_rating",
            "cast",
            "poster_url",
            "trailer_url",
        ]


class HallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hall
        fields = ["id", "name", "rows_count", "seats_per_row"]


class HallShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hall
        fields = ["id", "name"]


class SessionMovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ["id", "title", "poster_url", "age_rating"]


class SessionSerializer(serializers.ModelSerializer):
    movie = SessionMovieSerializer(read_only=True)
    hall = HallShortSerializer(read_only=True)
    movie_id = serializers.PrimaryKeyRelatedField(
        queryset=Movie.objects.all(), source="movie", write_only=True
    )
    hall_id = serializers.PrimaryKeyRelatedField(
        queryset=Hall.objects.all(), source="hall", write_only=True
    )

    class Meta:
        model = Session
        fields = ["id", "movie", "movie_id", "hall", "hall_id", "start_time", "price"]

    def validate_start_time(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("Сеанс не можна запланувати в минулому.")
        return value

    def validate(self, attrs):
        movie = attrs.get("movie", getattr(self.instance, "movie", None))
        hall = attrs.get("hall", getattr(self.instance, "hall", None))
        start = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end = start + timedelta(minutes=movie.duration_min)

        others = Session.objects.filter(
            hall=hall,
            start_time__lt=end,
            start_time__gt=start - timedelta(minutes=600),
        ).select_related("movie")
        if self.instance is not None:
            others = others.exclude(pk=self.instance.pk)

        for other in others:
            if other.end_time > start:
                local_start = timezone.localtime(other.start_time)
                raise ConflictError(
                    f"Зал «{hall.name}» у цей час зайнятий: "
                    f"сеанс «{other.movie.title}» о {local_start:%H:%M} "
                    f"{local_start:%d.%m.%Y}. Оберіть інший час або зал."
                )
        return attrs


class MovieSessionSerializer(serializers.ModelSerializer):
    hall = HallShortSerializer(read_only=True)

    class Meta:
        model = Session
        fields = ["id", "start_time", "hall", "price"]
