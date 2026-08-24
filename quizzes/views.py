from google.genai import errors as genai_errors
from pydantic import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from yt_dlp.utils import DownloadError

from .functions import (
    generate_and_save_quiz,
    get_quiz_for_request,
    get_user_quizzes,
)
from .serializers import QuizCreateSerializer, QuizSerializer


class QuizListView(APIView):
    """List and create quizzes for the authenticated user."""

    def get(self, request):
        """Return all quizzes of the current user."""
        quizzes = get_user_quizzes(request.user)
        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Generate and save a quiz from a YouTube URL."""
        serializer = QuizCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        video_url = serializer.validated_data["url"]
        try:
            quiz = generate_and_save_quiz(request.user, video_url)
        except (DownloadError, genai_errors.APIError, ValidationError):
            return self.generation_error_response()
        return Response(QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)

    def generation_error_response(self):
        """Return a failed quiz generation response."""
        return Response(
            {"detail": "Quiz generation failed."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class QuizDetailView(APIView):
    """Retrieve, update, or delete a specific quiz."""

    def get(self, request, quiz_id):
        """Return a quiz when the user may access it."""
        quiz, error = get_quiz_for_request(request.user, quiz_id)
        if error == "not_found":
            return self.not_found_response()
        if error == "forbidden":
            return self.forbidden_response()
        serializer = QuizSerializer(quiz)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, quiz_id):
        """Partially update an owned quiz."""
        quiz, error = get_quiz_for_request(request.user, quiz_id)
        if error == "not_found":
            return self.not_found_response()
        if error == "forbidden":
            return self.forbidden_response()
        serializer = QuizSerializer(quiz, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, quiz_id):
        """Delete an owned quiz."""
        quiz, error = get_quiz_for_request(request.user, quiz_id)
        if error == "not_found":
            return self.not_found_response()
        if error == "forbidden":
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
