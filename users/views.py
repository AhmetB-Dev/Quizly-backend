from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .functions import (
    blacklist_refresh_token,
    create_user_tokens,
    delete_auth_cookies,
    refresh_access_token,
    set_access_cookie,
    set_auth_cookies,
)
from .serializers import LoginSerializer, RegisterSerializer


class RegisterView(APIView):
    """Register a new Quizly user."""

    authentication_classes = []
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

    authentication_classes = []
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


class TokenRefreshView(APIView):
    """Refresh the access token using the refresh cookie."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """Create and store a new access token."""
        refresh_token = request.COOKIES.get("refresh_token")
        access_token = refresh_access_token(refresh_token)

        if access_token is None:
            return self.invalid_token_response()

        response = Response({"detail": "Token refreshed"})
        return set_access_cookie(response, access_token)

    def invalid_token_response(self):
        """Return an invalid refresh token response."""
        return Response(
            {"detail": "Invalid or missing refresh token."},
            status=status.HTTP_401_UNAUTHORIZED,
        )


class LogoutView(APIView):
    """Log out a Quizly user."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """Blacklist refresh token and delete cookies."""
        refresh_token = request.COOKIES.get("refresh_token")

        if not blacklist_refresh_token(refresh_token):
            return self.invalid_token_response()

        response = self.success_response()
        return delete_auth_cookies(response)

    def success_response(self):
        """Return the successful logout response."""
        return Response(
            {
                "detail": (
                    "Log-Out successfully! All Tokens will be deleted. "
                    "Refresh token is now invalid."
                )
            },
            status=status.HTTP_200_OK,
        )

    def invalid_token_response(self):
        """Return an invalid authentication response."""
        return Response(
            {"detail": "Invalid or missing refresh token."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
