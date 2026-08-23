from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class QuizlyUserAdmin(UserAdmin):
    """Configure Quizly users in the Django admin."""

    pass
