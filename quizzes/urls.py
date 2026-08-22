from django.urls import path

from .views import QuizDetailView, QuizListView


urlpatterns = [
    path("quizzes/", QuizListView.as_view(), name="quiz-list"),
    path(
        "quizzes/<int:quiz_id>/",
        QuizDetailView.as_view(),
        name="quiz-detail",
    ),
]
