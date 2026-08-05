import json

from google import genai

from app.settings import settings

_client = genai.Client(api_key=settings.gemini_api_key)

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
