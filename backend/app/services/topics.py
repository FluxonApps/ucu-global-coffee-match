import json
import logging
import os

from google import genai
from google.oauth2 import service_account

from app.settings import settings

logger = logging.getLogger(__name__)

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

GROUP_SYSTEM_PROMPT = """
You are an assistant for a corporate coffee chat application.

A group of colleagues has just been matched for a coffee chat.

Generate 3 to 5 engaging conversation starters that the ENTIRE GROUP can discuss.

Requirements:
- Include topics based on common interests whenever possible.
- If members have different interests, create questions that connect them.
- Questions should encourage everyone to participate.
- Keep each topic to one sentence.
- Write in English.
- Return ONLY a JSON array of strings.

Example:
[
  "Which technology has excited everyone the most recently?",
  "If each of you could recommend one book or podcast, what would it be?",
  "What's one skill you've learned recently that surprised you?"
]
"""


def _get_genai_client() -> genai.Client | None:
  creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or getattr(settings, "google_application_credentials", None)

  credentials = None
  if creds_path and os.path.exists(creds_path):
    try:
      credentials = service_account.Credentials.from_service_account_file(
        creds_path,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
      )
    except Exception as err:
      logger.warning(f"Failed to load credentials from {creds_path}: {err}")

  try:
    project_id = getattr(settings, "gemini_project_id", None) or os.getenv("GEMINI_PROJECT_ID")
    location = getattr(settings, "gemini_location", "us-central1") or os.getenv("GEMINI_LOCATION", "us-central1")

    return genai.Client(
      vertexai=True,
      project=project_id,
      location=location,
      credentials=credentials,
    )
  except Exception as exc:
    logger.warning(f"Failed to initialize GenAI client: {exc}")
    return None


def generate_conversation_topics(user1: dict, user2: dict) -> list[str]:
  """Generate conversation topic suggestions for two matched users, based on their interests."""
  client = _get_genai_client()
  if not client:
    return _fallback_topics()

  prompt = f"""Colleague A ({user1.get("first_name", "Person A")}):
- Interests: {_format_interests(user1)}

Colleague B ({user2.get("first_name", "Person B")}):
- Interests: {_format_interests(user2)}

Suggest 3 to 5 conversation topics for their coffee chat."""

  try:
    response = client.models.generate_content(
      model="gemini-2.5-flash",
      contents=prompt,
      config={
        "system_instruction": SYSTEM_PROMPT,
        "response_mime_type": "application/json",
      },
    )
    topics = json.loads(response.text or "[]")
    if isinstance(topics, list) and topics:
      return [str(topic) for topic in topics][:5]
    return _fallback_topics()
  except Exception as exc:  # keep matching flow working even if AI call fails
    logger.error(f"[topics] Failed to generate conversation topics: {exc}")
    return _fallback_topics()


def _fallback_group_topics() -> list[str]:
  return [
    "What's something interesting you've learned recently?",
    "Which technology or tool has improved your work the most?",
    "If you could instantly master one new skill, what would it be?",
    "What's the best piece of career advice you've received?",
    "What hobby outside of work would you recommend to everyone?",
  ]


def generate_group_conversation_topics(
  participants: list[dict],
) -> list[str]:
  """
  Generate conversation starters for an entire coffee chat group.
  """

  client = _get_genai_client()

  if not client:
    return _fallback_group_topics()

  participant_descriptions = []

  for participant in participants:
    participant_descriptions.append(
      f"""
Participant:
Name: {participant.get("first_name", "Unknown")}
Role: {participant.get("role_title") or "Unknown"}
Department: {participant.get("department") or "Unknown"}
Interests: {_format_interests(participant)}
Bio: {participant.get("bio") or ""}
"""
    )

  prompt = (
    "The following colleagues have been matched into one coffee chat group.\n\n"
    + "\n".join(participant_descriptions)
    + "\n\nGenerate 3 to 5 conversation starters for the whole group."
  )

  try:
    response = client.models.generate_content(
      model="gemini-2.5-flash",
      contents=prompt,
      config={
        "system_instruction": GROUP_SYSTEM_PROMPT,
        "response_mime_type": "application/json",
      },
    )

    topics = json.loads(response.text or "[]")

    if isinstance(topics, list) and topics:
      return [str(topic) for topic in topics][:5]

  except Exception as exc:
    logger.error(f"[topics] Failed to generate group conversation topics: {exc}")

  return _fallback_group_topics()


def _format_interests(user: dict) -> str:
  parts = []
  for field in ("personal_interests", "skills", "languages"):
    values = user.get(field) or []
    if values:
      if isinstance(values, list):
        parts.append(", ".join(values))
      elif isinstance(values, str):
        parts.append(values)
  return "; ".join(parts) if parts else "no listed interests"


def _fallback_topics() -> list[str]:
  return [
    "What's something you've been excited about at work recently?",
    "Any good books, shows, or podcasts you'd recommend?",
    "What do you like to do outside of work?",
  ]
