import json

from google import genai
from google.oauth2 import service_account
import logging
import os
from google.oauth2 import service_account
from google import genai
from app.settings import settings
from app.settings import settings

_credentials = (
    service_account.Credentials.from_service_account_file(
        settings.google_application_credentials,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    if settings.google_application_credentials
    else None
)

_client = genai.Client(
    vertexai=True,
    project=settings.gemini_project_id,
    location=settings.gemini_location,
    credentials=_credentials,
)

SYSTEM_PROMPT = """You are an assistant for a corporate "coffee chat" matching app.
Given the interests of two colleagues who have just been matched for a coffee chat,
suggest 3 to 5 short, specific conversation topics or icebreakers they could use to
start their conversation.

Topics should:
- Reference shared or complementary interests when possible
- Be friendly, casual, and easy to jump into
- Be phrased as a short question or prompt (one sentence each)
- Be written in English

Respond with ONLY a JSON array of strings, no other text, no markdown formatting.
Example: ["What's the most interesting thing you've built with Python recently?", "..."]
"""


def generate_conversation_topics(user1: dict, user2: dict) -> list[str]:
    """Generate conversation topic suggestions for two matched users, based on their interests."""
    prompt = f"""Colleague A ({user1.get("first_name", "Person A")}):
- Interests: {_format_interests(user1)}

Colleague B ({user2.get("first_name", "Person B")}):
- Interests: {_format_interests(user2)}

Suggest 3 to 5 conversation topics for their coffee chat."""

    try:
        response = _client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "system_instruction": SYSTEM_PROMPT,
                "response_mime_type": "application/json",
            },
        )
        topics = json.loads(response.text)
        if isinstance(topics, list) and topics:
            return [str(topic) for topic in topics][:5]
        return _fallback_topics()
    except Exception as exc:  # keep matching flow working even if AI call fails
        print(f"[topics] Failed to generate conversation topics: {exc}")
        return _fallback_topics()


def _format_interests(user: dict) -> str:
    parts = []
    for field in ("personal_interests", "skills", "languages"):
        values = user.get(field) or []
        if values:
            parts.append(", ".join(values))
    return "; ".join(parts) if parts else "no listed interests"


def _fallback_topics() -> list[str]:
    return [
        "What's something you've been excited about at work recently?",
        "Any good books, shows, or podcasts you'd recommend?",
        "What do you like to do outside of work?",
    ]


logger = logging.getLogger(__name__)

def get_credentials():
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or getattr(settings, "google_application_credentials", None)

    if creds_path and os.path.exists(creds_path):
        return service_account.Credentials.from_service_account_file(
            creds_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )

    logger.warning(f"Google credentials file not found at: {creds_path}")
    return None

def generate_conversation_topics(...) -> list[str]:
    credentials = get_credentials()
    if not credentials:
        # Резервний список тем, якщо файл секретів відсутній
        return [
            "Які ваші улюблені хобі?",
            "Про які проєкти вам найбільше подобається розповідати?",
            "Як ви зазвичай проводите вільний час?"
        ]

    # Створення клієнта та генерація тем...
