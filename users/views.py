from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .functions import create_user_tokens, set_auth_cookies
from .serializers import LoginSerializer, RegisterSerializer


class RegisterView(APIView):
    """Register a new Quizly user."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Validate registration data and create the user."""
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "User created successfully!"},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Authenticate a Quizly user."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Authenticate user and set JWT cookies."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        if user is None:
            return self.invalid_credentials_response()
        tokens = create_user_tokens(user)
        response = self.create_response(user)
        return set_auth_cookies(response, tokens)

    def invalid_credentials_response(self):
        """Return a generic login error."""
        return Response(
            {"detail": "Invalid credentials."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    def create_response(self, user):
        """Create the successful login response."""
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        }
        return Response(
            {"detail": "Login successfully!", "user": user_data},
            status=status.HTTP_200_OK,
        )
