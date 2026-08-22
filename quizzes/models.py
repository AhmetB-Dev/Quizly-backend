from django.conf import settings
from django.db import models


class Quiz(models.Model):
    """Represent a quiz created from a YouTube video."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quizzes",
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    video_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """Return the quiz title."""
        return self.title


class Question(models.Model):
    """Represent a question belonging to a quiz."""

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    question_title = models.TextField()
    question_options = models.JSONField(default=list)
    answer = models.TextField()
    position = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["quiz", "position"],
                name="unique_question_position_per_quiz",
            )
        ]

    def __str__(self):
        """Return the question title."""
        return self.question_title
