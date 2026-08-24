from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from google.genai import errors as genai_errors
from rest_framework import status
from rest_framework.test import APITestCase
from yt_dlp.utils import DownloadError

from users.functions import create_user_tokens

from .models import Quiz
from .schemas import GeneratedQuestion, GeneratedQuiz

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

    def create_generated_quiz(self):
        """Create mocked Gemini quiz data."""
        questions = [
            GeneratedQuestion(
                question_title=f"Question {index}",
                question_options=["A", "B", "C", "D"],
                answer="A",
            )
            for index in range(1, 11)
        ]
        return GeneratedQuiz(
            title="Generated Quiz",
            description="Generated description",
            questions=questions,
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

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

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

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_delete_own_quiz(self):
        """Delete an owned quiz."""
        response = self.client.delete(self.detail_url(self.quiz))

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertFalse(Quiz.objects.filter(id=self.quiz.id).exists())

    def test_delete_foreign_quiz_is_forbidden(self):
        """Reject deletion of another user's quiz."""
        response = self.client.delete(self.detail_url(self.other_quiz))

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    @patch("quizzes.functions.generate_quiz_from_youtube")
    def test_generation_error_returns_500(self, mock_generate):
        """Return 500 when quiz generation fails."""
        mock_generate.side_effect = genai_errors.ServerError(
            503,
            {"error": {"message": "Service unavailable"}},
            None,
        )

        response = self.client.post(
            reverse("quiz-list"),
            {"url": "https://www.youtube.com/watch?v=test"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @patch("quizzes.functions.generate_quiz_from_youtube")
    def test_create_quiz_successfully(self, mock_generate):
        """Create and store a generated quiz."""
        mock_generate.return_value = self.create_generated_quiz()

        response = self.client.post(
            reverse("quiz-list"),
            {"url": "https://www.youtube.com/watch?v=test"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        created_quiz = Quiz.objects.get(id=response.data["id"])
        self.assertEqual(created_quiz.user, self.user)
        self.assertEqual(created_quiz.questions.count(), 10)

    @patch("quizzes.functions.generate_quiz_from_youtube")
    def test_reject_non_youtube_url(self, mock_generate):
        """Reject URLs from unsupported websites."""
        response = self.client.post(
            reverse("quiz-list"),
            {"url": "https://example.com/video"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        mock_generate.assert_not_called()

    def test_create_quiz_requires_authentication(self):
        """Require authentication for quiz creation."""
        self.client.cookies.clear()

        response = self.client.post(
            reverse("quiz-list"),
            {"url": "https://www.youtube.com/watch?v=test"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    @patch("quizzes.functions.generate_quiz_from_youtube")
    def test_short_youtube_url_is_normalized(self, mock_generate):
        """Normalize shortened YouTube URLs."""
        mock_generate.return_value = self.create_generated_quiz()

        response = self.client.post(
            reverse("quiz-list"),
            {"url": "https://youtu.be/xQMigZK5gAY"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            response.data["video_url"],
            "https://www.youtube.com/watch?v=xQMigZK5gAY",
        )

    @patch("quizzes.functions.generate_quiz_from_youtube")
    def test_youtube_shorts_url_is_normalized(self, mock_generate):
        """Normalize YouTube Shorts URLs."""
        mock_generate.return_value = self.create_generated_quiz()

        response = self.client.post(
            reverse("quiz-list"),
            {"url": "https://www.youtube.com/shorts/xQMigZK5gAY"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            response.data["video_url"],
            "https://www.youtube.com/watch?v=xQMigZK5gAY",
        )

    @patch("quizzes.functions.generate_quiz_from_youtube")
    def test_youtube_embed_url_is_normalized(self, mock_generate):
        """Normalize YouTube embed URLs."""
        mock_generate.return_value = self.create_generated_quiz()

        response = self.client.post(
            reverse("quiz-list"),
            {"url": "https://www.youtube.com/embed/xQMigZK5gAY"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            response.data["video_url"],
            "https://www.youtube.com/watch?v=xQMigZK5gAY",
        )

    @patch("quizzes.functions.generate_quiz_from_youtube")
    def test_youtube_download_error_returns_500(self, mock_generate):
        """Return 500 when the YouTube download fails."""
        mock_generate.side_effect = DownloadError("Download failed")

        response = self.client.post(
            reverse("quiz-list"),
            {"url": "https://www.youtube.com/watch?v=test"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
