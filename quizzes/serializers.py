from urllib.parse import urlparse

from rest_framework import serializers

from .models import Question, Quiz


class QuizCreateSerializer(serializers.Serializer):
    """Validate input for quiz generation."""

    url = serializers.URLField()

    def validate_url(self, value):
        """Allow only YouTube URLs."""
        hostname = urlparse(value).hostname or ""
        is_youtube = (
            hostname == "youtu.be"
            or hostname == "youtube.com"
            or hostname.endswith(".youtube.com")
        )
        if not is_youtube:
            raise serializers.ValidationError("Only YouTube URLs are allowed.")
        return value


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
