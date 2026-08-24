from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

from .functions import is_access_token_blacklisted


class CookieJWTAuthentication(JWTAuthentication):
    """Authenticate users through the access-token cookie."""

    def authenticate(self, request):
        """Validate the access token stored in the cookie."""
        raw_token = request.COOKIES.get("access_token")
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)

        if is_access_token_blacklisted(validated_token):
            raise AuthenticationFailed("Token is blacklisted.")

        user = self.get_user(validated_token)
        return user, validated_token
