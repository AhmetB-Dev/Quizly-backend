from .models import Quiz


def get_user_quizzes(user):
    """Return all quizzes belonging to a user."""
    return (
        Quiz.objects.filter(user=user)
        .prefetch_related("questions")
        .order_by("-created_at")
    )


def get_quiz_by_id(quiz_id):
    """Return a quiz by ID or None."""
    try:
        return Quiz.objects.prefetch_related("questions").get(id=quiz_id)
    except Quiz.DoesNotExist:
        return None


def is_quiz_owner(user, quiz):
    """Check whether a quiz belongs to a user."""
    return quiz.user_id == user.id
