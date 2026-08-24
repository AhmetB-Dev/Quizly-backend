# Quizly Backend

Quizly is a Django REST API that allows authenticated users to generate quizzes from YouTube videos.

This repository contains my backend implementation for the Quizly project.

The frontend was provided by the Developer Akademie as part of the Backend course and was not developed by me.

Frontend repository:

[Developer Akademie – project.Quizly](https://github.com/Developer-Akademie-Backendkurs/project.Quizly)

The backend downloads the audio from a YouTube video, converts it with FFmpeg, transcribes it locally using Whisper AI and generates a structured quiz using Google Gemini Flash.

Each generated quiz contains exactly **10 questions with 4 answer options**.

---

## Quick Start

### 1. Create a virtual environment

```bash
py -3.11 -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Install FFmpeg

FFmpeg must be installed **globally** and must be available through the system PATH.

Verify the installation:

```bash
ffmpeg -version
```

Quiz generation will not work without FFmpeg.

### 4. Create the environment file

Create a `.env` file in the project root.

You can use `.env.example` as a template:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CORS_ALLOWED_ORIGINS=http://127.0.0.1:5500,http://localhost:5500
GEMINI_API_KEY=your-gemini-api-key
```

Never commit your real `.env` file or API keys.

### 5. Apply database migrations

```bash
python manage.py migrate
```

### 6. Start the backend

```bash
python manage.py runserver
```

The backend is then available at:

```text
http://127.0.0.1:8000/
```

### 7. Run the tests

```bash
python manage.py test
```

---

## Frontend

The frontend for Quizly was provided by the Developer Akademie Backend course.

It is not part of my own frontend implementation. My work in this project focuses on the Django backend, REST API, authentication, quiz generation pipeline, database integration and communication with the provided frontend.

Frontend repository:

[Developer Akademie – project.Quizly](https://github.com/Developer-Akademie-Backendkurs/project.Quizly)

The frontend and backend run separately and communicate through the REST API.

---

## Tech Stack

### Backend

- Python 3.11
- Django 5.2
- Django REST Framework
- SQLite

### Authentication

- JSON Web Tokens
- SimpleJWT
- HttpOnly Cookies
- Refresh Token Blacklisting

### Quiz Generation

- yt-dlp
- FFmpeg
- OpenAI Whisper
- Google Gemini Flash
- Pydantic

### Additional Packages

- django-cors-headers
- python-dotenv
- google-genai

---

## Features

### Authentication

- User registration
- User login
- JWT access token
- JWT refresh token
- HttpOnly authentication cookies
- Token refresh
- Logout
- Refresh token blacklisting
- Protected API endpoints

### Quiz Management

Authenticated users can:

- Create quizzes from YouTube videos
- View their quizzes
- View individual quizzes
- Update quiz titles
- Update quiz descriptions
- Delete quizzes
- Access only their own quizzes

### AI Quiz Generation

Quizly automatically:

1. Receives a YouTube URL
2. Downloads the audio using yt-dlp
3. Converts the audio using FFmpeg
4. Transcribes the audio locally using Whisper
5. Sends the transcript to Gemini Flash
6. Generates structured quiz data
7. Validates the generated data
8. Stores the quiz and questions in the database

Every generated quiz contains:

- A title
- A description
- Exactly 10 questions
- Exactly 4 answer options per question
- Exactly one correct answer per question

---

## Quiz Generation Pipeline

```text
YouTube URL
    ↓
yt-dlp
    ↓
FFmpeg
    ↓
MP3 Audio
    ↓
Whisper AI
    ↓
Transcript
    ↓
Google Gemini Flash
    ↓
Structured Quiz Data
    ↓
Pydantic Validation
    ↓
Django Database
```

Temporary audio files are automatically removed after transcription.

---

## Supported YouTube URLs

Only YouTube URLs are accepted for quiz generation.

Supported formats include:

```text
https://www.youtube.com/watch?v=VIDEO_ID
https://youtu.be/VIDEO_ID
https://www.youtube.com/shorts/VIDEO_ID
https://www.youtube.com/embed/VIDEO_ID
```

Supported URLs are normalized internally to:

```text
https://www.youtube.com/watch?v=VIDEO_ID
```

---

## Environment Variables

The application uses environment variables stored in a `.env` file.

Example:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CORS_ALLOWED_ORIGINS=http://127.0.0.1:5500,http://localhost:5500
GEMINI_API_KEY=your-gemini-api-key
```

The real `.env` file must not be committed to Git.

Use `.env.example` as a template.

---

## FFmpeg

FFmpeg is required for the YouTube audio processing pipeline.

It must be installed **globally** on the system.

Check whether FFmpeg is available:

```bash
ffmpeg -version
```

If the command is not recognized, FFmpeg is either not installed or has not been added to the system PATH.

FFmpeg is not installed through `requirements.txt` because it is a system dependency rather than a Python package.

---

## Whisper

OpenAI Whisper runs locally.

It is used to convert the extracted YouTube audio into text before the transcript is sent to Gemini.

Whisper performance depends on the available hardware and the length of the video.

CPU processing is supported but can take longer than GPU processing.

---

## Gemini

Google Gemini Flash is used to transform the Whisper transcript into structured quiz data.

A Gemini API key is required.

Add it to your `.env` file:

```env
GEMINI_API_KEY=your-gemini-api-key
```

The API key must never be committed to the repository.

---

## Authentication

Quizly uses JWT authentication with HttpOnly cookies.

After a successful login, the backend creates:

```text
access_token
refresh_token
```

Both tokens are stored in HttpOnly cookies.

The access token is used to authenticate protected API requests.

The refresh token can be used to generate a new access token.

On logout:

- Authentication cookies are removed
- The refresh token is blacklisted
- The blacklisted refresh token can no longer be used

---

## API Endpoints

### Registration

```http
POST /api/register/
```

Creates a new user.

---

### Login

```http
POST /api/login/
```

Authenticates the user and creates access and refresh tokens.

---

### Logout

```http
POST /api/logout/
```

Deletes authentication cookies and blacklists the refresh token.

Authentication required.

---

### Refresh Token

```http
POST /api/token/refresh/
```

Creates a new access token using the refresh token stored in the HttpOnly cookie.

---

## Quiz Endpoints

### Create Quiz

```http
POST /api/quizzes/
```

Example request:

```json
{
    "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

The backend processes the video and returns the generated quiz.

Authentication required.

---

### Get All Quizzes

```http
GET /api/quizzes/
```

Returns only quizzes belonging to the authenticated user.

---

### Get Quiz

```http
GET /api/quizzes/{id}/
```

Returns a specific quiz.

Users can only access their own quizzes.

---

### Update Quiz

```http
PATCH /api/quizzes/{id}/
```

Editable fields:

```json
{
    "title": "Updated title",
    "description": "Updated description"
}
```

Users can only update their own quizzes.

---

### Delete Quiz

```http
DELETE /api/quizzes/{id}/
```

Deletes an owned quiz.

---

## Permissions

Quizly uses authenticated API access by default.

Users can:

```text
Access own quiz       ✅
Edit own quiz         ✅
Delete own quiz       ✅

Access foreign quiz   ❌
Edit foreign quiz     ❌
Delete foreign quiz   ❌
```

Unauthorized access is rejected by the backend.

---

## Admin Panel

Django's administration interface is available at:

```text
http://127.0.0.1:8000/admin/
```

Create an administrator account with:

```bash
python manage.py createsuperuser
```

The admin panel supports management of:

- Users
- Quizzes
- Individual questions

Questions can also be managed directly within a quiz.

---

## Database

The development environment uses SQLite.

Apply migrations with:

```bash
python manage.py migrate
```

Create new migrations after model changes with:

```bash
python manage.py makemigrations
```

Then apply them:

```bash
python manage.py migrate
```

---

## Tests

Run all tests with:

```bash
python manage.py test
```

The backend currently includes automated tests covering:

- User registration
- User login
- Invalid login credentials
- JWT authentication
- Token refresh
- Invalid refresh tokens
- Missing refresh tokens
- Logout
- Refresh token blacklisting
- Quiz creation
- Quiz retrieval
- Quiz ownership
- Quiz updates
- Quiz deletion
- Authentication requirements
- YouTube URL validation
- YouTube URL normalization
- YouTube download errors
- Gemini/API generation errors

The current test suite contains:

```text
29 automated tests
```

---

## System Check

Django's project configuration can be checked with:

```bash
python manage.py check
```

A healthy configuration should return:

```text
System check identified no issues (0 silenced).
```

---

## Project Structure

```text
quizly-backend/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── users/
│   ├── authentication.py
│   ├── functions.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── quizzes/
│   ├── admin.py
│   ├── functions.py
│   ├── models.py
│   ├── schemas.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── .env.example
├── .gitignore
├── manage.py
├── requirements.txt
└── README.md
```

---

## Development Setup

Recommended development environment:

```text
Python: 3.11
Django: 5.2
```

Create the virtual environment:

```bash
py -3.11 -m venv .venv
```

Activate it:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Apply migrations:

```bash
python manage.py migrate
```

Start Django:

```bash
python manage.py runserver
```

---

## Security

The backend includes several security measures:

- Password hashing through Django
- JWT-based authentication
- HttpOnly cookies
- Refresh token blacklisting
- Environment variables for secrets
- User-based quiz ownership
- Protected API endpoints
- CORS configuration
- Server-side URL validation
- No API keys stored in source code

Sensitive values must always remain inside the local `.env` file.

---

## Notes

- FFmpeg must be installed globally.
- Whisper runs locally.
- Gemini requires an API key.
- Quiz generation time depends on video length and hardware performance.
- External services such as YouTube or Gemini may temporarily be unavailable.
- Temporary audio files are automatically deleted.
- The frontend is provided separately by the Developer Akademie.
- This repository focuses on the backend implementation.

---

## Frontend Credits

The Quizly frontend was provided by the **Developer Akademie** for the Backend course.

Frontend repository:

[Developer Akademie – project.Quizly](https://github.com/Developer-Akademie-Backendkurs/project.Quizly)

The frontend itself was not developed by me. My implementation covers the backend functionality and its integration with the provided frontend.
