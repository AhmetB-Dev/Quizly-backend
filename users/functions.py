from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken


def create_user_tokens(user):
    """Create access and refresh tokens for a user."""
    refresh_token = RefreshToken.for_user(user)
    return {
        "access_token": str(refresh_token.access_token),
        "refresh_token": str(refresh_token),
    }


def set_auth_cookies(response, tokens):
    """Store JWT tokens in secure HTTP-only cookies."""
    cookie_options = {
        "httponly": True,
        "secure": settings.JWT_COOKIE_SECURE,
        "samesite": "Lax",
        "path": "/",
    }
    response.set_cookie(
        "access_token",
        tokens["access_token"],
        **cookie_options,
    )
    response.set_cookie(
        "refresh_token",
        tokens["refresh_token"],
        **cookie_options,
    )
    return response
