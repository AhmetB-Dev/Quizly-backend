from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class LoginTests(APITestCase):
    """Tests the user login endpoint."""

    def setUp(self):
        """Prepare a user and the login endpoint."""
        self.url = reverse("login")
        self.password = "Test1234"
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password=self.password,
        )

    def login_user(self, password=None, username="testuser"):
        """Send a login request."""
        return self.client.post(
            self.url,
            {
                "username": username,
                "password": password or self.password,
            },
            format="json",
        )

    def test_login_successfully(self):
        """Log in with valid credentials."""
        response = self.login_user()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["username"], "testuser")
        self.assertEqual(response.data["user"]["email"], "test@example.com")

    def test_login_sets_auth_cookies(self):
        """Set access and refresh cookies after login."""
        response = self.login_user()

        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)
        self.assertTrue(response.cookies["access_token"]["httponly"])
        self.assertTrue(response.cookies["refresh_token"]["httponly"])

    def test_login_does_not_return_tokens_in_body(self):
        """Keep JWT tokens out of the response body."""
        response = self.login_user()

        self.assertNotIn("access_token", response.data)
        self.assertNotIn("refresh_token", response.data)

    def test_login_with_wrong_password(self):
        """Reject an incorrect password."""
        response = self.login_user(password="Wrong1234")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "Invalid credentials.")

    def test_login_with_unknown_username(self):
        """Reject an unknown username."""
        response = self.login_user(username="unknown")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "Invalid credentials.")


class RegisterTests(APITestCase):
    """Tests the user registration endpoint."""

    def setUp(self):
        """Prepare the registration endpoint."""
        self.url = reverse("register")
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "Test1234",
            "confirmed_password": "Test1234",
        }

    def register_user(self, data=None):
        """Send a registration request."""
        return self.client.post(
            self.url,
            data or self.user_data,
            format="json",
        )

    def test_register_user_successfully(self):
        """Register a user with valid data."""
        response = self.register_user()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data["detail"],
            "User created successfully!",
        )

    def test_register_duplicate_email(self):
        """Reject an already registered email."""
        self.register_user()
        data = self.user_data.copy()
        data["username"] = "seconduser"

        response = self.register_user(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_register_duplicate_username(self):
        """Reject an already registered username."""
        self.register_user()
        data = self.user_data.copy()
        data["email"] = "second@example.com"

        response = self.register_user(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_register_password_mismatch(self):
        """Reject mismatching passwords."""
        data = self.user_data.copy()
        data["confirmed_password"] = "Different123"

        response = self.register_user(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("confirmed_password", response.data)
