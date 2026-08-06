"""
Slack Bot that selects users from a PostgreSQL database for coffee matches.

Dependency Installation:
    pip install slack_bolt slack_sdk python-dotenv psycopg2-binary uvicorn fastapi

Run:
    python slack_random_user_bot.py

Create a .env file alongside this script before running:
    SLACK_BOT_TOKEN=xoxb-...
    SLACK_APP_TOKEN=xapp-1-...
    DATABASE_URL=postgresql://user:password@localhost:5432/slackbot_db

Required Bot OAuth Scopes (OAuth & Permissions -> Bot Token Scopes):
    - commands            (to receive slash commands)
    - chat:write          (to allow the bot to send messages to channels/DMs)
    - users:read          (to fetch Slack profile photos if missing in DB)
    - im:read             (to allow sending direct messages)

Configuration Steps in Slack App Console:
    1. Create Slash Command /random_user
    2. Create Slash Command /smart-match
    3. Create Slash Command /mute
    4. Create Slash Command /unmute
    5. Create Slash Command /login
    6. Create Slash Command /help
    7. Enable Socket Mode (Settings -> Socket Mode)
    8. Generate App-Level Token with 'connections:write' scope
    9. Under "Event Subscriptions" -> "Subscribe to bot events", add app_home_opened
    10. Under "App Home", enable the "Home" tab (Show Tabs -> Home Tab)
    11. Under "Interactivity & Shortcuts", enable Interactivity (required for /login modal)
    12. Reinstall app to workspace after scope/event updates
"""

import os
import sys
from pathlib import Path

# Вказуємо шлях до папки backend і додаємо її в sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Всі інші імпорти мають іти ПІСЛЯ коду вище
import json
import logging
import random
import threading

import db
import uvicorn
from app.services.topics import generate_conversation_topics
from dotenv import load_dotenv
from fastapi import FastAPI
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv()

logging.basicConfig(level=logging.INFO)

app = App(token=os.environ["SLACK_BOT_TOKEN"])

# File used to track users who have already received a welcome message.
WELCOMED_USERS_FILE = "welcomed_users.json"


def load_welcomed_users() -> set[str]:
    if not os.path.exists(WELCOMED_USERS_FILE):
        return set()
    with open(WELCOMED_USERS_FILE, "r", encoding="utf-8") as f:
        return set(json.load(f))


def save_welcomed_users(users: set[str]) -> None:
    with open(WELCOMED_USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(users), f, ensure_ascii=False, indent=2)


HELP_TEXT = (
    "*Available Commands:*\n\n"
    "• `/login CODE` — Link your Slack account to your website profile using your registration code "
    "(run `/login` without a code to open the input modal).\n"
    "• `/random_user` — Selects a random available user from the database and displays their profile.\n"
    "• `/smart-match` — Finds the best matching colleague based on shared interests and skills.\n"
    "• `/mute` — Pauses your availability (you won't be picked for matching).\n"
    "• `/unmute` — Resumes your availability for matching.\n"
    "• `/help` — Displays this list of available commands.\n\n"
    "You can also mention me (`@Global Coffee Connect`) in any channel to see available commands."
)


def resolve_avatar_url(client, db_user: dict) -> str:
    """
    Returns avatar URL: prioritizes custom photo from DB (avatar_url),
    falling back to Slack profile photo if missing or placeholder.
    """
    avatar_url = db_user.get("avatar_url")
    is_placeholder = not avatar_url or avatar_url == "/static/avatars/default.png"

    if is_placeholder and db_user.get("slack_user_id"):
        try:
            slack_profile = client.users_info(user=db_user["slack_user_id"])
            profile = slack_profile["user"].get("profile", {})
            avatar_url = (
                profile.get("image_192")
                or profile.get("image_512")
                or profile.get("image_72")
                or avatar_url
            )
        except Exception as e:
            logging.warning(f"Failed to fetch profile photo from Slack: {e}")

    return avatar_url


def build_user_card_blocks(client, db_user: dict, topics: list[str] | None = None) -> list[dict]:
    """Generates Block Kit payload with profile picture, interests and conversation topics."""
    full_name = f"{db_user['first_name']} {db_user['last_name']}".strip()
    slack_id = db_user["slack_user_id"]

    role = db_user.get("role_title") or "Not specified"
    dept = db_user.get("department") or "Not specified"
    bio = db_user.get("bio") or "Not specified"
    interests = db_user.get("personal_interests") or []
    interests_str = ", ".join(interests) if interests else "Not specified"
    skills = db_user.get("skills") or []
    skills_str = ", ".join(skills) if skills else "Not specified"

    avatar_url = resolve_avatar_url(client, db_user)

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"🎲 *Random User:* <@{slack_id}> ({full_name})\n"
                    f"💼 *Role:* {role} | *Department:* {dept}\n"
                    f"📝 *Bio:* {bio}\n"
                    f"🎯 *Interests:* {interests_str}\n"
                    f"💡 *Skills:* {skills_str}"
                ),
            },
            "accessory": {
                "type": "image",
                "image_url": avatar_url,
                "alt_text": full_name,
            },
        },
    ]

    if topics:
        topics_formatted = "\n".join([f"• {t}" for t in topics])
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"💬 *Conversation Starters:*\n{topics_formatted}",
                },
            }
        )

    return blocks


@app.command("/random_user")
def pick_random_user(ack, respond, command, client):
    """
    Slash command /random_user handler.
    Selects a random available user from the database (excluding requester
    and avoiding consecutive duplicate matches when possible).
    """
    ack()

    requester_slack_id = command["user_id"]

    try:
        candidates = db.get_registered_users(exclude_slack_id=requester_slack_id)
    except Exception as e:
        respond(f"Failed to retrieve user list from database: {e}")
        return

    if not candidates:
        respond("No available registered users found in the database.")
        return

    # Attempt to exclude the requester's most recent partner
    requester = db.get_user_by_slack_id(requester_slack_id)
    if requester:
        last_partner_id = db.get_last_match_partner_id(requester["id"])
        filtered = [u for u in candidates if u["id"] != last_partner_id]
        if filtered:
            candidates = filtered

    chosen_user = random.choice(candidates)

    # Generate conversation topics based on both users' interests
    topics = []
    if requester:
        try:
            topics = generate_conversation_topics(requester, chosen_user)
        except Exception as e:
            logging.warning(f"Failed to generate conversation topics: {e}")

    blocks = build_user_card_blocks(client, chosen_user, topics)
    respond(
        blocks=blocks,
        text=f"Random User: {chosen_user['first_name']} {chosen_user['last_name']}",
    )

    if requester:
        try:
            db.record_match(requester["id"], chosen_user["id"], topics)
        except Exception as e:
            logging.warning(f"Failed to record match in database: {e}")


@app.command("/smart-match")
def handle_smart_match_command(ack, body, client, respond):
    """Slash command /smart-match handler for AI/attribute-based matching."""
    ack()

    slack_user_id = body["user_id"]
    requester = db.get_user_by_slack_id(slack_user_id)
    if not requester:
        respond(
            "❌ Profile not found in system. Please register on the website and link your Slack account."
        )
        return

    match_result = db.find_best_match_for_user(requester["id"])
    if not match_result:
        respond(
            "😔 No available colleagues found for matching right now. Please try again later!"
        )
        return

    partner = match_result["candidate"]
    shared_interests = match_result["shared_interests"]

    # Generate icebreaker topics
    topics = generate_conversation_topics(requester, partner)

    # Save match to database
    db.create_smart_match(requester["id"], partner["id"], topics)

    topics_formatted = "\n".join([f"• {t}" for t in topics])
    shared_info = (
        f"\n🤝 *Shared Interests:* {', '.join(shared_interests)}"
        if shared_interests
        else ""
    )

    # 1. Send confirmation to requester
    respond(
        f"🎉 *We found an ideal coffee match for you!*\n\n"
        f"👤 *Partner:* <@{partner['slack_user_id']}> ({partner.get('first_name', '')} {partner.get('last_name', '')})\n"
        f"{shared_info}\n\n"
        f"💡 *Suggested Icebreaker Topics:*\n{topics_formatted}\n\n"
        f"Send a direct message to your colleague to schedule a coffee break! ☕"
    )

    # 2. Send notification to partner
    try:
        client.chat_postMessage(
            channel=partner["slack_user_id"],
            text=(
                f"👋 Hi there! <@{slack_user_id}> would like to connect with you for coffee!\n\n"
                f"{shared_info}\n\n"
                f"💡 *Ideas to start the conversation:*\n{topics_formatted}\n\n"
                f"Keep an eye out for a direct message! ☕"
            ),
        )
    except Exception as e:
        logging.error(f"Failed to send Slack notification to partner: {e}")


def try_login_with_code(code: str, slack_user_id: str) -> tuple[bool, str]:
    """Validates registration code and links Slack account to database user."""
    code = code.strip()

    if not code:
        return False, "Registration code cannot be empty."

    user = db.get_user_by_code(code)
    if not user:
        return False, "Invalid registration code. Please check and try again."

    try:
        db.link_slack_account(user["id"], slack_user_id)
    except Exception as e:
        return False, f"Code verified, but failed to link account: {e}"

    full_name = f"{user['first_name']} {user['last_name']}"
    return (
        True,
        f"✅ Login successful! Account *{full_name}* is now linked to your Slack user.",
    )


@app.command("/login")
def handle_login_command(ack, respond, command, body, client):
    """
    Slash command /login handler.
    If code is provided inline (/login CODE), process immediately.
    If run without code (/login), open modal dialog.
    """
    code = command.get("text", "").strip()

    if code:
        ack()
        success, message = try_login_with_code(code, command["user_id"])
        respond(message)
        return

    ack()
    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "login_modal_submit",
            "title": {"type": "plain_text", "text": "Account Login"},
            "submit": {"type": "plain_text", "text": "Log In"},
            "close": {"type": "plain_text", "text": "Cancel"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "code_block",
                    "label": {"type": "plain_text", "text": "Registration Code"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "code_input",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Enter code from website",
                        },
                    },
                },
            ],
        },
    )


@app.view("login_modal_submit")
def handle_login_submit(ack, body, client, view):
    """Processes modal submission for /login command."""
    code = view["state"]["values"]["code_block"]["code_input"]["value"] or ""
    slack_user_id = body["user"]["id"]

    success, message = try_login_with_code(code, slack_user_id)

    if not success:
        ack(response_action="errors", errors={"code_block": message})
        return

    ack()
    client.chat_postMessage(channel=slack_user_id, text=message)


@app.command("/mute")
def handle_mute_command(ack, respond, command):
    """Pauses user availability for matching."""
    ack()
    slack_user_id = command["user_id"]
    user = db.get_user_by_slack_id(slack_user_id)

    if not user:
        respond(
            "Your account is not linked to Slack yet. Please use `/login CODE` first."
        )
        return

    try:
        db.set_availability(slack_user_id, False)
        respond(
            "🔕 Mode updated! You are now **muted** and will not be selected for coffee matches. Use `/unmute` to re-enable."
        )
    except Exception as e:
        respond(f"Failed to update availability status: {e}")


@app.command("/unmute")
def handle_unmute_command(ack, respond, command):
    """Resumes user availability for matching."""
    ack()
    slack_user_id = command["user_id"]
    user = db.get_user_by_slack_id(slack_user_id)

    if not user:
        respond(
            "Your account is not linked to Slack yet. Please use `/login CODE` first."
        )
        return

    try:
        db.set_availability(slack_user_id, True)
        respond(
            "🔔 Mode updated! You are now **unmuted** and available for coffee matches."
        )
    except Exception as e:
        respond(f"Failed to update availability status: {e}")


@app.command("/help")
def show_help(ack, respond):
    """Slash command /help handler — prints command list."""
    ack()
    respond(HELP_TEXT)


@app.event("app_mention")
def handle_mention(event, say):
    """Responds with help guidance when the bot is mentioned in channels."""
    say(f"Hi <@{event['user']}>!\n\n{HELP_TEXT}")


@app.event("app_home_opened")
def update_home_tab(client, event, logger):
    """Оновлює вміст вкладки Home при її відкритті користувачем."""
    user_id = event["user"]

    # Отримуємо дані користувача з БД для динамічного відображення (за наявності)
    user = db.get_user_by_slack_id(user_id)

    if user:
        status_text = (
            "🟢 *Ваш статус:* Доступні для матчів"
            if user.get("is_available")
            else "🔴 *Ваш статус:* На паузі (Muted)"
        )
        account_info = f"👤 *Профіль:* {user.get('first_name')} {user.get('last_name')} ({user.get('email')})"
    else:
        status_text = "⚠️ *Акаунт не прив'язано!* Скористайтеся командою `/login CODE`."
        account_info = (
            "Прив'яжіть акаунт з веб-сайту, щоб брати участь у кава-зустрічах."
        )

    try:
        client.views_publish(
            user_id=user_id,
            view={
                "type": "home",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "☕ Вітаємо в Global Coffee Connect!",
                        },
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Тут ви можете керувати своїм профілем та дізнаватися про доступні можливості.",
                        },
                    },
                    {"type": "divider"},
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"{account_info}\n\n{status_text}",
                        },
                    },
                    {"type": "divider"},
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": (
                                "*📌 Доступні команди:*\n\n"
                                "• `/login CODE` — Прив'язати акаунт з сайту\n"
                                "• `/smart-match` — Знайти ідеального партнера для кави\n"
                                "• `/random_user` — Випадковий вибір колеги\n"
                                "• `/mute` / `/unmute` — Пауза або відновлення участі\n"
                                "• `/help` — Довідка"
                            ),
                        },
                    },
                ],
            },
        )
    except Exception as e:
        logger.error(f"Помилка оновлення Home tab: {e}")


@app.event("message")
def handle_message_events(body, logger):
    """Silently handles general message events to suppress Slack 404 warning logs."""


# FastAPI web app for Render health checks
web_app = FastAPI()


@web_app.api_route("/", methods=["GET", "HEAD"])
@web_app.api_route("/health", methods=["GET", "HEAD"])
def health_check():
    return {"status": "ok"}


def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(web_app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    # Start web server in background thread for cloud host health checks
    threading.Thread(target=run_web_server, daemon=True).start()

    # Start Slack Socket Mode handler
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
