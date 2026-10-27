from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Director, Genre, Hall, Movie, Session


class CinemaApiTestCase(APITestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name="Фантастика")
        self.director = Director.objects.create(first_name="Дені", last_name="Вільнев")
        self.movie = Movie.objects.create(
            title="Дюна: Частина друга",
            director=self.director,
            duration_min=166,
            release_year=2024,
            age_rating="12+",
        )
        self.movie.genres.add(self.genre)
        self.hall = Hall.objects.create(name="Зал 1", rows_count=10, seats_per_row=14)
        self.start = timezone.now() + timedelta(days=1)

    def assert_error_format(self, response, expected_status):
        self.assertEqual(response.status_code, expected_status)
        self.assertIn("error", response.data)
        self.assertIn("details", response.data)


class MovieApiTests(CinemaApiTestCase):
    def test_list_is_paginated(self):
        response = self.client.get("/api/v1/movies")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], self.movie.title)

    def test_search_is_case_insensitive_for_cyrillic(self):
        response = self.client.get("/api/v1/movies", {"search": "ДЮНА"})
        self.assertEqual(response.data["count"], 1)
        response = self.client.get("/api/v1/movies", {"search": "вільнев"})
        self.assertEqual(response.data["count"], 1)

    def test_invalid_filter_returns_400(self):
        response = self.client.get("/api/v1/movies", {"genre": "abc"})
        self.assert_error_format(response, status.HTTP_400_BAD_REQUEST)

    def test_create_movie(self):
        data = {
            "title": "Прибуття",
            "director_id": self.director.id,
            "genre_ids": [self.genre.id],
            "duration_min": 116,
            "release_year": 2016,
            "age_rating": "12+",
        }
        response = self.client.post("/api/v1/movies", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["director"]["id"], self.director.id)
        self.assertEqual(response.data["genres"][0]["name"], "Фантастика")

    def test_create_movie_with_invalid_data_returns_400(self):
        response = self.client.post("/api/v1/movies", {"title": ""}, format="json")
        self.assert_error_format(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn("director_id", response.data["details"])

    def test_update_movie(self):
        response = self.client.patch(
            f"/api/v1/movies/{self.movie.id}", {"age_rating": "16+"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["age_rating"], "16+")

    def test_missing_movie_returns_404(self):
        response = self.client.get("/api/v1/movies/999")
        self.assert_error_format(response, status.HTTP_404_NOT_FOUND)

    def test_movie_with_sessions_cannot_be_deleted(self):
        Session.objects.create(
            movie=self.movie, hall=self.hall, start_time=self.start, price=180
        )
        response = self.client.delete(f"/api/v1/movies/{self.movie.id}")
        self.assert_error_format(response, status.HTTP_409_CONFLICT)
        self.assertTrue(Movie.objects.filter(pk=self.movie.id).exists())


class DirectorApiTests(CinemaApiTestCase):
    def test_director_movies(self):
        response = self.client.get(f"/api/v1/directors/{self.director.id}/movies")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_director_with_movies_cannot_be_deleted(self):
        response = self.client.delete(f"/api/v1/directors/{self.director.id}")
        self.assert_error_format(response, status.HTTP_409_CONFLICT)

    def test_director_without_movies_can_be_deleted(self):
        director = Director.objects.create(first_name="Крістофер", last_name="Нолан")
        response = self.client.delete(f"/api/v1/directors/{director.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class GenreApiTests(CinemaApiTestCase):
    def test_duplicate_genre_returns_400(self):
        response = self.client.post(
            "/api/v1/genres", {"name": "Фантастика"}, format="json"
        )
        self.assert_error_format(response, status.HTTP_400_BAD_REQUEST)

    def test_genre_with_movies_cannot_be_deleted(self):
        response = self.client.delete(f"/api/v1/genres/{self.genre.id}")
        self.assert_error_format(response, status.HTTP_409_CONFLICT)
        self.assertIn("фільмів: 1", response.data["error"])
        self.assertTrue(Genre.objects.filter(id=self.genre.id).exists())

    def test_genre_without_movies_can_be_deleted(self):
        genre = Genre.objects.create(name="Комедія")
        response = self.client.delete(f"/api/v1/genres/{genre.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Genre.objects.filter(id=genre.id).exists())


class HallApiTests(CinemaApiTestCase):
    def test_hall_with_sessions_cannot_be_deleted(self):
        Session.objects.create(
            movie=self.movie, hall=self.hall, start_time=self.start, price=180
        )
        response = self.client.delete(f"/api/v1/halls/{self.hall.id}")
        self.assert_error_format(response, status.HTTP_409_CONFLICT)


class SessionApiTests(CinemaApiTestCase):
    def session_data(self, start):
        return {
            "movie_id": self.movie.id,
            "hall_id": self.hall.id,
            "start_time": start.isoformat(),
            "price": 180,
        }

    def test_create_session(self):
        response = self.client.post(
            "/api/v1/sessions", self.session_data(self.start), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["hall"]["name"], "Зал 1")

    def test_session_in_past_returns_400(self):
        past = timezone.now() - timedelta(days=1)
        response = self.client.post(
            "/api/v1/sessions", self.session_data(past), format="json"
        )
        self.assert_error_format(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn("start_time", response.data["details"])

    def test_overlapping_session_returns_409(self):
        Session.objects.create(
            movie=self.movie, hall=self.hall, start_time=self.start, price=180
        )
        overlapping = self.start + timedelta(minutes=60)
        response = self.client.post(
            "/api/v1/sessions", self.session_data(overlapping), format="json"
        )
        self.assert_error_format(response, status.HTTP_409_CONFLICT)

    def test_session_after_previous_one_is_allowed(self):
        Session.objects.create(
            movie=self.movie, hall=self.hall, start_time=self.start, price=180
        )
        later = self.start + timedelta(minutes=self.movie.duration_min + 15)
        response = self.client.post(
            "/api/v1/sessions", self.session_data(later), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_sessions_list_filtered_by_date(self):
        Session.objects.create(
            movie=self.movie, hall=self.hall, start_time=self.start, price=180
        )
        date = timezone.localtime(self.start).date().isoformat()
        response = self.client.get("/api/v1/sessions", {"date": date})
        self.assertEqual(response.data["count"], 1)
