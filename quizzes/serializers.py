from rest_framework import serializers

from .models import Question, Quiz


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
