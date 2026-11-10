from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

VALID_USER = {
    "username": "olena",
    "email": "olena@example.com",
    "password": "StrongPass123",
    "password_confirm": "StrongPass123",
}


class RegisterTests(APITestCase):
    def test_register_success(self):
        response = self.client.post("/api/v1/auth/register", VALID_USER, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", response.data)
        user = User.objects.get(username="olena")
        self.assertNotEqual(user.password, "StrongPass123")
        self.assertTrue(user.check_password("StrongPass123"))

    def test_register_invalid_data(self):
        data = {
            "username": "",
            "email": "bad",
            "password": "123",
            "password_confirm": "1",
        }
        response = self.client.post("/api/v1/auth/register", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        for field in ["username", "email", "password"]:
            self.assertIn(field, response.data["details"])

    def test_passwords_do_not_match(self):
        data = {**VALID_USER, "password_confirm": "OtherPass123"}
        response = self.client.post("/api/v1/auth/register", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirm", response.data["details"])

    def test_duplicate_username(self):
        self.client.post("/api/v1/auth/register", VALID_USER, format="json")
        data = {**VALID_USER, "email": "other@example.com"}
        response = self.client.post("/api/v1/auth/register", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data["details"])


class AuthTests(APITestCase):
    def setUp(self):
        User.objects.create_user(username="olena", password="StrongPass123")

    def login(self):
        data = {"username": "olena", "password": "StrongPass123"}
        return self.client.post("/api/v1/auth/login", data, format="json")

    def test_login_returns_tokens(self):
        response = self.login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_wrong_password(self):
        data = {"username": "olena", "password": "wrong"}
        response = self.client.post("/api/v1/auth/login", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_returns_new_access(self):
        refresh = self.login().data["refresh"]
        response = self.client.post(
            "/api/v1/auth/refresh", {"refresh": refresh}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_me_requires_token(self):
        response = self.client.get("/api/v1/users/me")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_with_token(self):
        access = self.login().data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.get("/api/v1/users/me")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "olena")


class PermissionTests(APITestCase):
    def test_anyone_can_read(self):
        response = self.client.get("/api/v1/genres")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_anonymous_cannot_create(self):
        response = self.client.post("/api/v1/genres", {"name": "Драма"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_cannot_create(self):
        user = User.objects.create_user(username="olena", password="StrongPass123")
        self.client.force_authenticate(user=user)
        response = self.client.post("/api/v1/genres", {"name": "Драма"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create(self):
        admin = User.objects.create_user(
            username="admin", password="AdminPass123", is_staff=True
        )
        self.client.force_authenticate(user=admin)
        response = self.client.post("/api/v1/genres", {"name": "Драма"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
