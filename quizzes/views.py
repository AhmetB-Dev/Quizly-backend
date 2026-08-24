from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .functions import (
    generate_quiz_from_youtube,
    get_quiz_by_id,
    get_user_quizzes,
    is_quiz_owner,
    save_generated_quiz,
)
from .serializers import QuizCreateSerializer, QuizSerializer


class QuizListView(APIView):
    """List and create quizzes for the authenticated user."""

    def get(self, request):
        """Return all quizzes of the current user."""
        quizzes = get_user_quizzes(request.user)
        serializer = QuizSerializer(quizzes, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Generate and save a quiz from a YouTube URL."""
        input_serializer = QuizCreateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        video_url = input_serializer.validated_data["url"]
        generated_quiz = generate_quiz_from_youtube(video_url)
        quiz = save_generated_quiz(
            request.user,
            video_url,
            generated_quiz,
        )
        output_serializer = QuizSerializer(quiz)
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class QuizDetailView(APIView):
    """Retrieve, update, or delete a specific quiz."""

    def get(self, request, quiz_id):
        """Return a quiz when the user may access it."""
        quiz = get_quiz_by_id(quiz_id)

        if quiz is None:
            return self.not_found_response()
        if not is_quiz_owner(request.user, quiz):
            return self.forbidden_response()

        serializer = QuizSerializer(quiz)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, quiz_id):
        """Partially update an owned quiz."""
        quiz = get_quiz_by_id(quiz_id)

        if quiz is None:
            return self.not_found_response()
        if not is_quiz_owner(request.user, quiz):
            return self.forbidden_response()

        serializer = QuizSerializer(quiz, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, quiz_id):
        """Delete an owned quiz."""
        quiz = get_quiz_by_id(quiz_id)

        if quiz is None:
            return self.not_found_response()
        if not is_quiz_owner(request.user, quiz):
            return self.forbidden_response()

        quiz.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def not_found_response(self):
        """Return a quiz-not-found response."""
        return Response(
            {"detail": "Quiz not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    def forbidden_response(self):
        """Return a forbidden quiz response."""
        return Response(
            {"detail": "Access denied."},
            status=status.HTTP_403_FORBIDDEN,
        )
