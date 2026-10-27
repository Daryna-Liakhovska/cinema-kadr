from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import ConflictError
from .filters import get_choice_param, get_date_param, get_int_param, search_queryset
from .models import Director, Genre, Hall, Movie, Session
from .pagination import StandardPagination
from .serializers import (
    DirectorListSerializer,
    DirectorSerializer,
    GenreSerializer,
    HallSerializer,
    MovieListSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    SessionSerializer,
)

NOT_FOUND_MESSAGES = {
    Movie: "Фільм з id={pk} не знайдено.",
    Director: "Режисера з id={pk} не знайдено.",
    Genre: "Жанр з id={pk} не знайдено.",
    Hall: "Зал з id={pk} не знайдено.",
    Session: "Сеанс з id={pk} не знайдено.",
}

MOVIE_ORDERING = {
    "title",
    "-title",
    "release_year",
    "-release_year",
    "duration_min",
    "-duration_min",
}
DIRECTOR_ORDERING = {"last_name", "-last_name"}
SESSION_ORDERING = {"start_time", "-start_time", "price", "-price"}


def get_object(model, pk):
    try:
        return model.objects.get(pk=pk)
    except model.DoesNotExist:
        raise NotFound(NOT_FOUND_MESSAGES[model].format(pk=pk))


def paginated_response(request, view, queryset, serializer_class):
    paginator = StandardPagination()
    page = paginator.paginate_queryset(queryset, request, view=view)
    serializer = serializer_class(page, many=True)
    return paginator.get_paginated_response(serializer.data)


def filter_movies(request, queryset):
    genre = get_int_param(request, "genre")
    director = get_int_param(request, "director")
    age_rating = get_choice_param(
        request, "age_rating", {value for value, _ in Movie.AGE_RATINGS}
    )
    show_date = get_date_param(request, "date")
    ordering = get_choice_param(request, "ordering", MOVIE_ORDERING)

    if genre is not None:
        queryset = queryset.filter(genres__id=genre)
    if director is not None:
        queryset = queryset.filter(director_id=director)
    if age_rating:
        queryset = queryset.filter(age_rating=age_rating)
    if show_date:
        queryset = queryset.filter(sessions__start_time__date=show_date)
    queryset = queryset.distinct()

    queryset = search_queryset(
        queryset,
        request.query_params.get("search"),
        lambda movie: f"{movie.title} {movie.director}",
    )
    if ordering:
        queryset = queryset.order_by(ordering)
    return queryset.select_related("director").prefetch_related("genres")


class MovieListView(APIView):
    def get(self, request):
        movies = filter_movies(request, Movie.objects.all())
        return paginated_response(request, self, movies, MovieListSerializer)

    def post(self, request):
        serializer = MovieSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MovieDetailView(APIView):
    def get(self, request, pk):
        movie = get_object(Movie, pk)
        return Response(MovieSerializer(movie).data)

    def patch(self, request, pk):
        movie = get_object(Movie, pk)
        serializer = MovieSerializer(movie, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        movie = get_object(Movie, pk)
        sessions_count = movie.sessions.count()
        if sessions_count:
            raise ConflictError(
                f"Неможливо видалити фільм «{movie.title}», оскільки для нього "
                f"створено сеансів: {sessions_count}. Спочатку видаліть сеанси."
            )
        movie.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MovieSessionsView(APIView):
    def get(self, request, pk):
        movie = get_object(Movie, pk)
        sessions = movie.sessions.filter(start_time__gte=timezone.now())
        show_date = get_date_param(request, "date")
        if show_date:
            sessions = sessions.filter(start_time__date=show_date)
        sessions = sessions.select_related("hall")
        return Response(MovieSessionSerializer(sessions, many=True).data)


class DirectorListView(APIView):
    def get(self, request):
        directors = Director.objects.all()
        ordering = get_choice_param(request, "ordering", DIRECTOR_ORDERING)
        directors = search_queryset(
            directors,
            request.query_params.get("search"),
            lambda director: f"{director.first_name} {director.last_name}",
        )
        if ordering:
            directors = directors.order_by(ordering)
        return paginated_response(request, self, directors, DirectorListSerializer)

    def post(self, request):
        serializer = DirectorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DirectorDetailView(APIView):
    def get(self, request, pk):
        director = get_object(Director, pk)
        return Response(DirectorSerializer(director).data)

    def patch(self, request, pk):
        director = get_object(Director, pk)
        serializer = DirectorSerializer(director, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        director = get_object(Director, pk)
        movies_count = director.movies.count()
        if movies_count:
            raise ConflictError(
                f"Неможливо видалити режисера {director}, оскільки за ним "
                f"закріплено фільмів: {movies_count}. Спочатку видаліть ці фільми "
                f"або призначте їм іншого режисера."
            )
        director.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DirectorMoviesView(APIView):
    def get(self, request, pk):
        director = get_object(Director, pk)
        movies = filter_movies(request, director.movies.all())
        return paginated_response(request, self, movies, MovieListSerializer)


class GenreListView(APIView):
    def get(self, request):
        return Response(GenreSerializer(Genre.objects.all(), many=True).data)

    def post(self, request):
        serializer = GenreSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class GenreDetailView(APIView):
    def patch(self, request, pk):
        genre = get_object(Genre, pk)
        serializer = GenreSerializer(genre, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        genre = get_object(Genre, pk)
        movies_count = genre.movies.count()
        if movies_count:
            raise ConflictError(
                f"Неможливо видалити жанр «{genre.name}», оскільки до нього "
                f"прив'язано фільмів: {movies_count}. Спочатку приберіть цей жанр "
                f"у фільмів або видаліть їх."
            )
        genre.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class HallListView(APIView):
    def get(self, request):
        return Response(HallSerializer(Hall.objects.all(), many=True).data)

    def post(self, request):
        serializer = HallSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class HallDetailView(APIView):
    def get(self, request, pk):
        hall = get_object(Hall, pk)
        return Response(HallSerializer(hall).data)

    def patch(self, request, pk):
        hall = get_object(Hall, pk)
        serializer = HallSerializer(hall, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        hall = get_object(Hall, pk)
        sessions_count = hall.sessions.count()
        if sessions_count:
            raise ConflictError(
                f"Неможливо видалити зал «{hall.name}», оскільки в ньому "
                f"заплановано сеансів: {sessions_count}. Спочатку видаліть сеанси."
            )
        hall.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SessionListView(APIView):
    def get(self, request):
        show_date = get_date_param(request, "date") or timezone.localdate()
        movie = get_int_param(request, "movie")
        hall = get_int_param(request, "hall")
        ordering = get_choice_param(request, "ordering", SESSION_ORDERING)

        sessions = Session.objects.filter(start_time__date=show_date)
        if movie is not None:
            sessions = sessions.filter(movie_id=movie)
        if hall is not None:
            sessions = sessions.filter(hall_id=hall)
        if ordering:
            sessions = sessions.order_by(ordering)
        sessions = sessions.select_related("movie", "hall")
        return paginated_response(request, self, sessions, SessionSerializer)

    def post(self, request):
        serializer = SessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SessionDetailView(APIView):
    def get(self, request, pk):
        session = get_object(Session, pk)
        return Response(SessionSerializer(session).data)

    def patch(self, request, pk):
        session = get_object(Session, pk)
        serializer = SessionSerializer(session, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        session = get_object(Session, pk)
        session.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
