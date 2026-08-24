import os
import tempfile
from django.db import transaction
import whisper
import yt_dlp
from google import genai
from google.genai import types

from .models import Question, Quiz
from .schemas import GeneratedQuiz

QUIZ_PROMPT = """
Create a quiz using only the information from this transcript.

Requirements:
- exactly 10 meaningful questions
- exactly one correct answer per question
- create a suitable title
- create a short description
- do not invent facts not supported by the transcript

Transcript:
{transcript}
"""


def build_quiz_prompt(transcript):
    """Build the prompt used to generate a quiz."""
    return QUIZ_PROMPT.format(transcript=transcript)


def get_gemini_client():
    """Return the configured Gemini client."""
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def get_user_quizzes(user):
    """Return all quizzes belonging to a user."""
    return (
        Quiz.objects.filter(user=user)
        .prefetch_related("questions")
        .order_by("-created_at")
    )


def get_quiz_by_id(quiz_id):
    """Return a quiz by ID or None."""
    try:
        return Quiz.objects.prefetch_related("questions").get(id=quiz_id)
    except Quiz.DoesNotExist:
        return None


def is_quiz_owner(user, quiz):
    """Check whether a quiz belongs to a user."""
    return quiz.user_id == user.id


def get_audio_options(output_path):
    """Return yt-dlp options for audio extraction."""
    return {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
            }
        ],
    }


def download_youtube_audio(video_url, directory):
    """Download YouTube audio as an MP3 file."""
    output_path = os.path.join(directory, "audio.%(ext)s")
    options = get_audio_options(output_path)

    with yt_dlp.YoutubeDL(options) as downloader:
        downloader.download([video_url])

    return os.path.join(directory, "audio.mp3")


def transcribe_audio(audio_path):
    """Transcribe an audio file with Whisper."""
    model = whisper.load_model("tiny")
    result = model.transcribe(audio_path)
    return result["text"].strip()


def create_transcript_from_youtube(video_url):
    """Create a transcript from a YouTube video."""
    with tempfile.TemporaryDirectory() as directory:
        audio_path = download_youtube_audio(video_url, directory)
        return transcribe_audio(audio_path)


def generate_quiz_from_transcript(transcript):
    """Generate structured quiz data from a transcript."""
    client = get_gemini_client()
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=build_quiz_prompt(transcript),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=GeneratedQuiz.model_json_schema(),
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            ),
        ),
    )
    return GeneratedQuiz.model_validate_json(response.text)


def generate_quiz_from_youtube(video_url):
    """Generate quiz data from a YouTube video."""
    transcript = create_transcript_from_youtube(video_url)
    return generate_quiz_from_transcript(transcript)


def build_questions(quiz, generated_questions):
    """Build question models for a generated quiz."""
    return [
        Question(
            quiz=quiz,
            position=index,
            question_title=question.question_title,
            question_options=question.question_options,
            answer=question.answer,
        )
        for index, question in enumerate(generated_questions, start=1)
    ]


@transaction.atomic
def save_generated_quiz(user, video_url, generated_quiz):
    """Save a generated quiz and its questions."""
    quiz = Quiz.objects.create(
        user=user,
        title=generated_quiz.title,
        description=generated_quiz.description,
        video_url=video_url,
    )
    questions = build_questions(quiz, generated_quiz.questions)
    Question.objects.bulk_create(questions)
    return quiz
