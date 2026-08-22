from django.conf import settings
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken


def get_cookie_options():
    """Return common authentication cookie settings."""
    return {
        "httponly": True,
        "secure": settings.JWT_COOKIE_SECURE,
        "samesite": "Lax",
        "path": "/",
    }


def create_user_tokens(user):
    """Create access and refresh tokens for a user."""
    refresh_token = RefreshToken.for_user(user)
    return {
        "access_token": str(refresh_token.access_token),
        "refresh_token": str(refresh_token),
    }


def set_access_cookie(response, access_token):
    """Store the access token in an HTTP-only cookie."""
    response.set_cookie(
        "access_token",
        access_token,
        **get_cookie_options(),
    )
    return response


def set_refresh_cookie(response, refresh_token):
    """Store the refresh token in an HTTP-only cookie."""
    response.set_cookie(
        "refresh_token",
        refresh_token,
        **get_cookie_options(),
    )
    return response


def set_auth_cookies(response, tokens):
    """Store both JWT authentication cookies."""
    set_access_cookie(response, tokens["access_token"])
    set_refresh_cookie(response, tokens["refresh_token"])
    return response


def refresh_access_token(refresh_token):
    """Create a new access token from a refresh token."""
    if not refresh_token:
        return None
    try:
        token = RefreshToken(refresh_token)
        return str(token.access_token)
    except TokenError:
        return None


def blacklist_refresh_token(refresh_token):
    """Blacklist a refresh token."""
    if not refresh_token:
        return False

    try:
        RefreshToken(refresh_token).blacklist()
        return True
    except TokenError:
        return False


def delete_auth_cookies(response):
    """Delete authentication cookies."""
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return response
