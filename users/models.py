from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Represents a Quizly user."""

    email = models.EmailField(unique=True)


class BlacklistedAccessToken(models.Model):
    """Represent a revoked JWT access token."""

    jti = models.CharField(max_length=255, unique=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        """Return the token identifier."""
        return self.jti
