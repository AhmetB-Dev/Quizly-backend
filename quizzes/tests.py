from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from google.genai import errors as genai_errors
from rest_framework import status
from rest_framework.test import APITestCase
from yt_dlp.utils import DownloadError

from users.functions import create_user_tokens

from . import functions
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

    def create_generated_question(self, index):
        """Create one mocked Gemini question."""
        return GeneratedQuestion(
            question_title=f"Question {index}",
            question_options=["A", "B", "C", "D"],
            answer="A",
        )

    def create_generated_quiz(self):
        """Create mocked Gemini quiz data."""
        questions = [
            self.create_generated_question(index)
            for index in range(1, 11)
        ]
        return GeneratedQuiz(
            title="Generated Quiz",
            description="Generated description",
            questions=questions,
        )

    def post_quiz(self, url):
        """Send a quiz creation request."""
        return self.client.post(
            reverse("quiz-list"),
            {"url": url},
            format="json",
        )

    def assert_created_video_url(self, response, video_url):
        """Assert successful creation and normalized video URL."""
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["video_url"], video_url)

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
        response = self.post_quiz("https://www.youtube.com/watch?v=test")
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @patch("quizzes.functions.generate_quiz_from_youtube")
    def test_create_quiz_successfully(self, mock_generate):
        """Create and store a generated quiz."""
        mock_generate.return_value = self.create_generated_quiz()
        response = self.post_quiz("https://www.youtube.com/watch?v=test")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_quiz = Quiz.objects.get(id=response.data["id"])
        self.assertEqual(created_quiz.user, self.user)
        self.assertEqual(created_quiz.questions.count(), 10)

    @patch("quizzes.functions.generate_quiz_from_youtube")
    def test_reject_non_youtube_url(self, mock_generate):
        """Reject URLs from unsupported websites."""
        response = self.post_quiz("https://example.com/video")

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        mock_generate.assert_not_called()

    def test_create_quiz_requires_authentication(self):
        """Require authentication for quiz creation."""
        self.client.cookies.clear()
        response = self.post_quiz("https://www.youtube.com/watch?v=test")

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    @patch("quizzes.functions.generate_quiz_from_youtube")
    def test_short_youtube_url_is_normalized(self, mock_generate):
        """Normalize shortened YouTube URLs."""
        mock_generate.return_value = self.create_generated_quiz()
        response = self.post_quiz("https://youtu.be/xQMigZK5gAY")
        self.assert_created_video_url(
            response,
            "https://www.youtube.com/watch?v=xQMigZK5gAY",
        )

    @patch("quizzes.functions.generate_quiz_from_youtube")
    def test_youtube_shorts_url_is_normalized(self, mock_generate):
        """Normalize YouTube Shorts URLs."""
        mock_generate.return_value = self.create_generated_quiz()
        response = self.post_quiz(
            "https://www.youtube.com/shorts/xQMigZK5gAY"
        )
        self.assert_created_video_url(
            response,
            "https://www.youtube.com/watch?v=xQMigZK5gAY",
        )

    @patch("quizzes.functions.generate_quiz_from_youtube")
    def test_youtube_embed_url_is_normalized(self, mock_generate):
        """Normalize YouTube embed URLs."""
        mock_generate.return_value = self.create_generated_quiz()
        response = self.post_quiz(
            "https://www.youtube.com/embed/xQMigZK5gAY"
        )
        self.assert_created_video_url(
            response,
            "https://www.youtube.com/watch?v=xQMigZK5gAY",
        )

    @patch("quizzes.functions.generate_quiz_from_youtube")
    def test_youtube_download_error_returns_500(self, mock_generate):
        """Return 500 when the YouTube download fails."""
        mock_generate.side_effect = DownloadError("Download failed")
        response = self.post_quiz("https://www.youtube.com/watch?v=test")

        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class QuizFunctionTests(APITestCase):
    """Test quiz helper and generation functions."""

    def create_generated_question(self, index):
        """Create valid generated question data."""
        return GeneratedQuestion(
            question_title=f"Question {index}",
            question_options=["A", "B", "C", "D"],
            answer="A",
        )

    def create_generated_quiz(self):
        """Create valid generated quiz data."""
        questions = [
            self.create_generated_question(index)
            for index in range(1, 11)
        ]
        return GeneratedQuiz(
            title="Generated Quiz",
            description="Generated description",
            questions=questions,
        )

    def test_build_quiz_prompt(self):
        """Insert transcript content into the Gemini prompt."""
        prompt = functions.build_quiz_prompt("Python transcript")
        self.assertIn("Python transcript", prompt)
        self.assertIn("exactly 10 meaningful questions", prompt)

    @patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"})
    @patch("quizzes.functions.genai.Client")
    def test_get_gemini_client(self, mock_client):
        """Create Gemini client with configured API key."""
        functions.get_gemini_client()
        mock_client.assert_called_once_with(api_key="test-key")

    def test_get_generation_config(self):
        """Create structured Gemini generation configuration."""
        config = functions.get_generation_config()
        self.assertEqual(config.response_mime_type, "application/json")
        self.assertTrue(config.automatic_function_calling.disable)

    def test_missing_quiz_returns_not_found(self):
        """Return not found when a quiz does not exist."""
        user = User.objects.create_user(
            username="helperuser",
            email="helper@example.com",
            password="Test1234",
        )
        quiz, error = functions.get_quiz_for_request(user, 999999)
        self.assertIsNone(quiz)
        self.assertEqual(error, "not_found")

    def test_get_audio_options(self):
        """Create yt-dlp audio extraction options."""
        options = functions.get_audio_options("audio.%(ext)s")
        processor = options["postprocessors"][0]
        self.assertEqual(options["format"], "bestaudio/best")
        self.assertEqual(options["outtmpl"], "audio.%(ext)s")
        self.assertEqual(processor["preferredcodec"], "mp3")

    @patch("quizzes.functions.yt_dlp.YoutubeDL")
    def test_download_youtube_audio(self, mock_youtube_dl):
        """Download audio with yt-dlp without network access."""
        downloader = mock_youtube_dl.return_value.__enter__.return_value
        path = functions.download_youtube_audio(
            "https://youtube.com/watch?v=test",
            "temp",
        )
        downloader.download.assert_called_once()
        self.assertTrue(path.endswith("audio.mp3"))

    @patch("quizzes.functions.whisper.load_model")
    def test_transcribe_audio(self, mock_load_model):
        """Transcribe audio using the configured Whisper model."""
        model = mock_load_model.return_value
        model.transcribe.return_value = {"text": "  Hello World  "}
        transcript = functions.transcribe_audio("audio.mp3")
        mock_load_model.assert_called_once_with("tiny")
        model.transcribe.assert_called_once_with("audio.mp3")
        self.assertEqual(transcript, "Hello World")

    @patch("quizzes.functions.transcribe_audio", return_value="Transcript")
    @patch("quizzes.functions.download_youtube_audio", return_value="audio.mp3")
    def test_create_transcript_from_youtube(self, mock_download, mock_transcribe):
        """Create transcript from mocked YouTube audio."""
        result = functions.create_transcript_from_youtube("youtube-url")
        self.assertEqual(result, "Transcript")
        mock_download.assert_called_once()
        mock_transcribe.assert_called_once_with("audio.mp3")

    @patch("quizzes.functions.get_gemini_client")
    def test_generate_quiz_from_transcript(self, mock_client):
        """Parse structured quiz data returned by Gemini."""
        generated = self.create_generated_quiz()
        response = mock_client.return_value.models.generate_content.return_value
        response.text = generated.model_dump_json()
        result = functions.generate_quiz_from_transcript("Transcript")
        self.assertEqual(result.title, "Generated Quiz")
        self.assertEqual(len(result.questions), 10)

    @patch("quizzes.functions.generate_quiz_from_transcript")
    @patch(
        "quizzes.functions.create_transcript_from_youtube",
        return_value="Transcript",
    )
    def test_generate_quiz_from_youtube(self, mock_transcript, mock_generate):
        """Generate quiz data from a mocked YouTube transcript."""
        expected = self.create_generated_quiz()
        mock_generate.return_value = expected
        result = functions.generate_quiz_from_youtube("youtube-url")
        self.assertEqual(result, expected)
        mock_generate.assert_called_once_with("Transcript")
