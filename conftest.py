from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from cinema.models import Director, Hall, Movie, Session


def login(username, password):
    client = APIClient()
    response = client.post(
        reverse("login"),
        {"username": username, "password": password},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return client


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="viewer", password="ViewerPass123")


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        username="manager", password="ManagerPass123", is_staff=True
    )


@pytest.fixture
def user_client(user):
    return login("viewer", "ViewerPass123")


@pytest.fixture
def staff_client(staff_user):
    return login("manager", "ManagerPass123")


@pytest.fixture
def movie(db):
    director = Director.objects.create(first_name="Дені", last_name="Вільнев")
    return Movie.objects.create(
        title="Дюна: Частина друга",
        director=director,
        duration_min=166,
        release_year=2024,
        age_rating="12+",
    )


@pytest.fixture
def hall(db):
    return Hall.objects.create(name="Зал 1", rows_count=10, seats_per_row=14)


@pytest.fixture
def start_time():
    return timezone.now() + timedelta(days=1)


@pytest.fixture
def session(movie, hall, start_time):
    return Session.objects.create(
        movie=movie, hall=hall, start_time=start_time, price=180
    )
