from urllib.parse import parse_qs, urlparse

from rest_framework import serializers

from .models import Question, Quiz


class QuizCreateSerializer(serializers.Serializer):
    """Validate input for quiz generation."""

    url = serializers.URLField()

    def validate_url(self, value):
        """Validate and normalize a YouTube URL."""
        parsed = urlparse(value)
        hostname = (parsed.hostname or "").lower()
        video_id = self.get_video_id(parsed, hostname)

        if not video_id:
            raise serializers.ValidationError("A valid YouTube URL is required.")

        return f"https://www.youtube.com/watch?v={video_id}"

    def get_video_id(self, parsed, hostname):
        """Extract the video ID from a YouTube URL."""
        path_parts = [part for part in parsed.path.split("/") if part]

        if hostname == "youtu.be":
            return path_parts[0] if path_parts else None

        if hostname not in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
            return None

        return self.get_youtube_path_id(parsed, path_parts)

    def get_youtube_path_id(self, parsed, path_parts):
        """Extract an ID from standard YouTube URL formats."""
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]

        if len(path_parts) >= 2 and path_parts[0] in {"shorts", "embed"}:
            return path_parts[1]

        return None


class QuestionSerializer(serializers.ModelSerializer):
    """Serialize quiz questions."""

    class Meta:
        model = Question
        fields = (
            "id",
            "question_title",
            "question_options",
            "answer",
            "created_at",
            "updated_at",
        )

    def validate_question_options(self, options):
        """Ensure every question has four answer options."""
        if len(options) != 4:
            raise serializers.ValidationError(
                "Exactly four answer options are required."
            )
        return options

    def validate(self, attrs):
        """Ensure the correct answer is one of the options."""
        options = attrs.get("question_options", [])
        answer = attrs.get("answer")

        if answer not in options:
            raise serializers.ValidationError(
                {"answer": "Answer must match one of the options."}
            )
        return attrs


class QuizSerializer(serializers.ModelSerializer):
    """Serialize quizzes including their questions."""

    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = (
            "id",
            "title",
            "description",
            "created_at",
            "updated_at",
            "video_url",
            "questions",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "video_url",
            "questions",
        )

    def get_youtube_video_id(self, parsed):
        """Extract a video ID from a YouTube URL."""
        path_parts = parsed.path.strip("/").split("/")

        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]

        if path_parts[0] in {"shorts", "embed"} and len(path_parts) > 1:
            return path_parts[1]

        return None
