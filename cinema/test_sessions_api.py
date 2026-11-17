from datetime import timedelta

import pytest
from django.utils import timezone

from cinema.models import Session

SESSIONS_URL = "/api/v1/sessions"


def session_url(pk):
    return f"{SESSIONS_URL}/{pk}"


def session_payload(movie, hall, start_time, price=180):
    return {
        "movie_id": movie.id,
        "hall_id": hall.id,
        "start_time": start_time.isoformat(),
        "price": price,
    }


@pytest.mark.django_db
def test_list_sessions_by_date(api_client, session):
    date = timezone.localtime(session.start_time).date().isoformat()
    response = api_client.get(SESSIONS_URL, {"date": date})
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["movie"]["title"] == session.movie.title


@pytest.mark.django_db
def test_list_sessions_empty(api_client):
    response = api_client.get(SESSIONS_URL, {"date": "2030-01-01"})
    assert response.status_code == 200
    assert response.data["count"] == 0
    assert response.data["results"] == []


@pytest.mark.django_db
def test_list_sessions_invalid_date_returns_400(api_client):
    response = api_client.get(SESSIONS_URL, {"date": "01.01.2030"})
    assert response.status_code == 400
    assert "date" in response.data["details"]


@pytest.mark.django_db
def test_get_session(api_client, session):
    response = api_client.get(session_url(session.id))
    assert response.status_code == 200
    assert response.data["hall"]["name"] == session.hall.name


@pytest.mark.django_db
def test_get_missing_session_returns_404(api_client):
    response = api_client.get(session_url(999))
    assert response.status_code == 404
    assert "error" in response.data


@pytest.mark.django_db
def test_admin_creates_session(staff_client, movie, hall, start_time):
    response = staff_client.post(
        SESSIONS_URL, session_payload(movie, hall, start_time), format="json"
    )
    assert response.status_code == 201
    assert response.data["movie"]["id"] == movie.id
    assert Session.objects.count() == 1


@pytest.mark.django_db
def test_create_session_without_token_returns_401(api_client, movie, hall, start_time):
    response = api_client.post(
        SESSIONS_URL, session_payload(movie, hall, start_time), format="json"
    )
    assert response.status_code == 401
    assert Session.objects.count() == 0


@pytest.mark.django_db
def test_create_session_with_invalid_token_returns_401(
    api_client, movie, hall, start_time
):
    api_client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
    response = api_client.post(
        SESSIONS_URL, session_payload(movie, hall, start_time), format="json"
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_regular_user_cannot_create_session(user_client, movie, hall, start_time):
    response = user_client.post(
        SESSIONS_URL, session_payload(movie, hall, start_time), format="json"
    )
    assert response.status_code == 403
    assert Session.objects.count() == 0


@pytest.mark.django_db
def test_create_session_with_invalid_data_returns_400(staff_client):
    response = staff_client.post(SESSIONS_URL, {"price": -5}, format="json")
    assert response.status_code == 400
    for field in ["movie_id", "hall_id", "start_time", "price"]:
        assert field in response.data["details"]


@pytest.mark.django_db
def test_create_session_in_past_returns_400(staff_client, movie, hall):
    past = timezone.now() - timedelta(days=1)
    response = staff_client.post(
        SESSIONS_URL, session_payload(movie, hall, past), format="json"
    )
    assert response.status_code == 400
    assert "start_time" in response.data["details"]


@pytest.mark.django_db
def test_create_overlapping_session_returns_409(staff_client, session):
    overlapping = session.start_time + timedelta(minutes=60)
    response = staff_client.post(
        SESSIONS_URL,
        session_payload(session.movie, session.hall, overlapping),
        format="json",
    )
    assert response.status_code == 409
    assert Session.objects.count() == 1


@pytest.mark.django_db
def test_create_session_after_previous_one_ends(staff_client, session):
    later = session.start_time + timedelta(minutes=session.movie.duration_min + 15)
    response = staff_client.post(
        SESSIONS_URL,
        session_payload(session.movie, session.hall, later),
        format="json",
    )
    assert response.status_code == 201


@pytest.mark.django_db
def test_admin_updates_session_price(staff_client, session):
    response = staff_client.patch(
        session_url(session.id), {"price": 200}, format="json"
    )
    assert response.status_code == 200
    session.refresh_from_db()
    assert session.price == 200


@pytest.mark.django_db
def test_regular_user_cannot_update_session(user_client, session):
    response = user_client.patch(session_url(session.id), {"price": 1}, format="json")
    assert response.status_code == 403
    session.refresh_from_db()
    assert session.price == 180


@pytest.mark.django_db
def test_update_missing_session_returns_404(staff_client):
    response = staff_client.patch(session_url(999), {"price": 200}, format="json")
    assert response.status_code == 404


@pytest.mark.django_db
def test_admin_deletes_session(staff_client, session):
    response = staff_client.delete(session_url(session.id))
    assert response.status_code == 204
    assert not Session.objects.filter(id=session.id).exists()


@pytest.mark.django_db
def test_delete_session_without_token_returns_401(api_client, session):
    response = api_client.delete(session_url(session.id))
    assert response.status_code == 401
    assert Session.objects.filter(id=session.id).exists()


@pytest.mark.django_db
def test_delete_missing_session_returns_404(staff_client):
    response = staff_client.delete(session_url(999))
    assert response.status_code == 404
