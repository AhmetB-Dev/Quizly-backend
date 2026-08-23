from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.functions import create_user_tokens

from .models import Question, Quiz


User = get_user_model()


class QuizApiTests(APITestCase):
    """Test quiz API endpoints and ownership."""

    def setUp(self):
        """Create users and test quizzes."""
        self.user = self.create_user("user1", "user1@example.com")
        self.other_user = self.create_user("user2", "user2@example.com")
        self.quiz = self.create_quiz(self.user, "Python Quiz")
        self.other_quiz = self.create_quiz(self.other_user, "Java Quiz")
        self.authenticate(self.user)

    def create_user(self, username, email):
        """Create a test user."""
        return User.objects.create_user(
            username=username,
            email=email,
            password="Test1234",
        )

    def create_quiz(self, user, title):
        """Create a quiz for a user."""
        return Quiz.objects.create(
            user=user,
            title=title,
            description="Test description",
            video_url="https://www.youtube.com/watch?v=test",
        )

    def authenticate(self, user):
        """Authenticate through the access-token cookie."""
        tokens = create_user_tokens(user)
        self.client.cookies["access_token"] = tokens["access_token"]

    def detail_url(self, quiz):
        """Return a quiz detail URL."""
        return reverse(
            "quiz-detail",
            kwargs={"quiz_id": quiz.id},
        )

    def test_get_own_quizzes(self):
        """Return only quizzes belonging to the user."""
        response = self.client.get(reverse("quiz-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.quiz.id)

    def test_get_own_quiz(self):
        """Return an owned quiz."""
        response = self.client.get(self.detail_url(self.quiz))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Python Quiz")

    def test_get_foreign_quiz_is_forbidden(self):
        """Reject access to another user's quiz."""
        response = self.client.get(self.detail_url(self.other_quiz))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_own_quiz(self):
        """Update an owned quiz."""
        response = self.client.patch(
            self.detail_url(self.quiz),
            {"title": "Updated Quiz"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Quiz")

    def test_patch_foreign_quiz_is_forbidden(self):
        """Reject updates to another user's quiz."""
        response = self.client.patch(
            self.detail_url(self.other_quiz),
            {"title": "Changed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_own_quiz(self):
        """Delete an owned quiz."""
        response = self.client.delete(self.detail_url(self.quiz))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Quiz.objects.filter(id=self.quiz.id).exists())

    def test_delete_foreign_quiz_is_forbidden(self):
        """Reject deletion of another user's quiz."""
        response = self.client.delete(self.detail_url(self.other_quiz))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
