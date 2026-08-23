from django.contrib import admin

from .models import Question, Quiz


class QuestionInline(admin.TabularInline):
    """Display questions directly inside a quiz."""

    model = Question
    extra = 0
    fields = (
        "position",
        "question_title",
        "question_options",
        "answer",
    )
    ordering = ("position",)


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Configure quizzes in the Django admin."""

    list_display = (
        "id",
        "title",
        "user",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "title",
        "description",
        "user__username",
        "user__email",
    )
    list_filter = ("created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")
    inlines = (QuestionInline,)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Configure questions in the Django admin."""

    list_display = (
        "id",
        "question_title",
        "quiz",
        "position",
    )
    search_fields = (
        "question_title",
        "quiz__title",
    )
    ordering = ("quiz", "position")
    readonly_fields = ("created_at", "updated_at")
