from django.urls import path

from . import views

urlpatterns = [
    path("movies", views.MovieListView.as_view(), name="movie-list"),
    path("movies/<int:pk>", views.MovieDetailView.as_view(), name="movie-detail"),
    path(
        "movies/<int:pk>/sessions",
        views.MovieSessionsView.as_view(),
        name="movie-sessions",
    ),
    path("directors", views.DirectorListView.as_view(), name="director-list"),
    path(
        "directors/<int:pk>",
        views.DirectorDetailView.as_view(),
        name="director-detail",
    ),
    path(
        "directors/<int:pk>/movies",
        views.DirectorMoviesView.as_view(),
        name="director-movies",
    ),
    path("genres", views.GenreListView.as_view(), name="genre-list"),
    path("genres/<int:pk>", views.GenreDetailView.as_view(), name="genre-detail"),
    path("halls", views.HallListView.as_view(), name="hall-list"),
    path("halls/<int:pk>", views.HallDetailView.as_view(), name="hall-detail"),
    path("sessions", views.SessionListView.as_view(), name="session-list"),
    path(
        "sessions/<int:pk>",
        views.SessionDetailView.as_view(),
        name="session-detail",
    ),
]
