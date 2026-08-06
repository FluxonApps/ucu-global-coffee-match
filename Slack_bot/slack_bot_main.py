"""
Slack-бот, який за командою /random_user вибирає випадкового
зареєстрованого користувача з бази даних PostgreSQL.

Встановлення залежностей:
    pip install slack_bolt slack_sdk python-dotenv psycopg2-binary

Запуск:
    python slack_random_user_bot.py

Перед запуском створи файл .env поруч зі скриптом:
    SLACK_BOT_TOKEN=xoxb-...
    SLACK_APP_TOKEN=xapp-1-...
    DATABASE_URL=postgresql://user:password@localhost:5432/slackbot_db

Потрібні OAuth Scopes для бота (OAuth & Permissions -> Bot Token Scopes):
    - commands            (щоб отримувати slash-команди)
    - chat:write          (щоб бот міг писати в канал/DM)
    - users:read          (щоб отримати фото профілю з Slack, якщо в базі немає avatar_url)
    - im:read              (щоб бот міг писати в особисті повідомлення)

Тепер випадковий користувач вибирається НЕ з учасників Slack-каналу,
а з таблиці users у PostgreSQL (тобто саме серед тих, хто зареєструвався
на сайті й прив'язав свій Slack-акаунт через slack_user_id).

Не забудь:
    1. Створити Slash Command /random_user в розділі "Slash Commands"
    2. Створити Slash Command /help в розділі "Slash Commands"
    3. Створити Slash Command /login в розділі "Slash Commands"
    4. Увімкнути Socket Mode (Settings -> Socket Mode)
    5. Згенерувати App-Level Token зі scope connections:write
    6. У розділі "Event Subscriptions" -> "Subscribe to bot events" додати
       подію app_home_opened (потрібна для привітального повідомлення)
    7. У розділі "App Home" увімкнути вкладку "Home" (Show Tabs -> Home Tab)
    8. У розділі "Interactivity & Shortcuts" увімкнути Interactivity
       (потрібно для модальних вікон /login)
    9. Перевстановити застосунок у workspace після зміни scopes/подій
"""

import json
import logging
import os
import random
import threading

import db
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv()

logging.basicConfig(level=logging.INFO)

app = App(token=os.environ["SLACK_BOT_TOKEN"])

# Файл, у якому зберігаємо ID користувачів, яким уже надсилали привітання.
# Це проста персистентність на файлі — для продакшену краще замінити
# на базу даних (SQLite/PostgreSQL), але для старту достатньо.
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
    "*Доступні команди:*\n\n"
    "• `/login КОД` — прив'язати свій Slack до акаунта на сайті, "
    "використовуючи код реєстрації (якщо ввести `/login` без коду, "
    "відкриється форма для вводу).\n"
    "• `/random_user` — вибирає випадкового зареєстрованого користувача "
    "з бази й показує його ім'я та фото профілю.\n"
    "• `/distarb on` / `/distarb off` — керує режимом «не турбувати»: "
    "`off` прибирає тебе з вибірки `/random_user`, `on` повертає назад.\n"
    "• `/help` — показує це повідомлення зі списком команд.\n\n"
    "Також можеш просто згадати мене (`@Global Coffee Connect`) в каналі — "
    "я підкажу, що вміти."
)


def resolve_avatar_url(client, db_user: dict) -> str:
    """
    Повертає URL аватарки: пріоритет — власне фото з бази (avatar_url),
    якщо це дефолтна заглушка або порожньо — падаємо назад на фото
    профілю зі Slack.
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
            logging.warning(f"Не вдалося отримати фото профілю зі Slack: {e}")

    return avatar_url


def build_user_card_blocks(client, db_user: dict) -> list[dict]:
    """Формує Block Kit-розмітку з фото профілю та іменем користувача з бази."""
    full_name = f"{db_user['first_name']} {db_user['last_name']}".strip()
    slack_id = db_user["slack_user_id"]

    details = []
    if db_user.get("role_title"):
        details.append(db_user["role_title"])
    if db_user.get("department"):
        details.append(db_user["department"])
    details_line = " · ".join(details)

    text = f"🎲 *Випадковий користувач:* <@{slack_id}> ({full_name})"
    if details_line:
        text += f"\n_{details_line}_"

    avatar_url = resolve_avatar_url(client, db_user)

    return [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": text},
            "accessory": {
                "type": "image",
                "image_url": avatar_url,
                "alt_text": full_name,
            },
        }
    ]


@app.command("/random_user")
def pick_random_user(ack, respond, command, client):
    """
    Обробник slash-команди /random_user.
    Вибирає випадкового зареєстрованого користувача з бази даних
    (виключаючи того, хто викликав команду, і, за можливості,
    того, з ким уже був останній метч).
    """
    ack()  # обов'язково підтверджуємо отримання команди протягом 3 секунд

    requester_slack_id = command["user_id"]

    try:
        candidates = db.get_registered_users(exclude_slack_id=requester_slack_id)
    except Exception as e:
        respond(f"Не вдалося отримати список користувачів з бази: {e}")
        return

    if not candidates:
        respond("У базі поки немає зареєстрованих користувачів для вибору.")
        return

    # Намагаємось не повторювати останній метч того, хто викликав команду
    requester = db.get_user_by_slack_id(requester_slack_id)
    if requester:
        last_partner_id = db.get_last_match_partner_id(requester["id"])
        filtered = [u for u in candidates if u["id"] != last_partner_id]
        if filtered:  # якщо після фільтрації хоч хтось лишився — використовуємо
            candidates = filtered

    chosen_user = random.choice(candidates)

    blocks = build_user_card_blocks(client, chosen_user)
    respond(
        blocks=blocks,
        text=f"Випадковий користувач: {chosen_user['first_name']} {chosen_user['last_name']}",
        # text — фолбек для сповіщень/клієнтів, що не рендерять blocks
    )

    # Записуємо метч у базу, якщо відомо, хто викликав команду
    if requester:
        try:
            db.record_match(requester["id"], chosen_user["id"])
        except Exception as e:
            logging.warning(f"Не вдалося записати метч у базу: {e}")


def try_login_with_code(code: str, slack_user_id: str) -> tuple[bool, str]:
    """
    Перевіряє код реєстрації і прив'язує Slack-акаунт до знайденого
    користувача. Повертає (успіх: bool, повідомлення: str).
    """
    code = code.strip()

    if not code:
        return False, "Код не може бути порожнім."

    user = db.get_user_by_code(code)
    if not user:
        return False, "Невірний код. Перевір і спробуй ще раз."

    try:
        db.link_slack_account(user["id"], slack_user_id)
    except Exception as e:
        return False, f"Код правильний, але не вдалося прив'язати акаунт: {e}"

    full_name = f"{user['first_name']} {user['last_name']}"
    return (
        True,
        f"✅ Успішний вхід! Акаунт *{full_name}* тепер прив'язаний до твого Slack.",
    )


@app.command("/login")
def handle_login_command(ack, respond, command, body, client):
    """
    Обробник slash-команди /login.
    Якщо код переданий одразу (/login АБВ123) — перевіряємо без модалки.
    Якщо код не переданий (просто /login) — відкриваємо модальне вікно
    з одним полем для вводу коду.
    """
    code = command.get("text", "").strip()

    if code:
        ack()
        success, message = try_login_with_code(code, command["user_id"])
        respond(message)
        return

    # Код не переданий одразу — відкриваємо модалку
    ack()
    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "login_modal_submit",
            "title": {"type": "plain_text", "text": "Вхід в акаунт"},
            "submit": {"type": "plain_text", "text": "Увійти"},
            "close": {"type": "plain_text", "text": "Скасувати"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "code_block",
                    "label": {"type": "plain_text", "text": "Код реєстрації"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "code_input",
                        "placeholder": {"type": "plain_text", "text": "Код із сайту"},
                    },
                },
            ],
        },
    )


@app.view("login_modal_submit")
def handle_login_submit(ack, body, client, view):
    """Обробляє відправку форми /login (коли код вводили через модалку)."""
    code = view["state"]["values"]["code_block"]["code_input"]["value"] or ""
    slack_user_id = body["user"]["id"]

    success, message = try_login_with_code(code, slack_user_id)

    if not success:
        ack(response_action="errors", errors={"code_block": message})
        return

    ack()  # закриває модалку
    client.chat_postMessage(channel=slack_user_id, text=message)


@app.command("/distarb")
def set_disturb_status(ack, respond, command):
    """
    Обробник slash-команди /distarb on|off.
    /distarb on  — дозволити, щоб тебе показували іншим у /random_user.
    /distarb off — увімкнути "не турбувати": тебе тимчасово не показуватимуть.
    """
    ack()

    arg = command.get("text", "").strip().lower()

    if arg not in ("on", "off"):
        respond(
            "Використання: `/distarb on` — дозволити турбувати, або `/distarb off` — не турбувати."
        )
        return

    slack_user_id = command["user_id"]
    user = db.get_user_by_slack_id(slack_user_id)

    if not user:
        respond(
            "Твій акаунт ще не прив'язаний до Slack. "
            "Спочатку виконай `/login КОД` із кодом реєстрації."
        )
        return

    new_status = arg == "on"

    try:
        db.set_availability(slack_user_id, new_status)
    except Exception as e:
        respond(f"Не вдалося змінити статус: {e}")
        return

    if new_status:
        respond("🔔 `/distarb on` — тебе знову можуть вибрати в `/random_user`.")
    else:
        respond(
            "🔕 `/distarb off` — режим «не турбувати» увімкнено, тебе тимчасово не показуватимуть."
        )


@app.command("/help")
def show_help(ack, respond):
    """Обробник slash-команди /help — показує список команд за бажанням."""
    ack()
    respond(HELP_TEXT)


@app.event("app_mention")
def handle_mention(event, say):
    """Опційно: якщо бота згадали текстом, підказуємо команду."""
    say(f"Привіт, <@{event['user']}>!\n\n{HELP_TEXT}")


@app.event("app_home_opened")
def handle_first_open(event, client):
    """
    Спрацьовує щоразу, коли користувач відкриває вкладку бота (Home)
    або заходить у DM з ним. Надсилаємо привітання з переліком команд
    лише один раз для кожного користувача.
    """
    user_id = event["user"]

    welcomed_users = load_welcomed_users()
    if user_id in welcomed_users:
        return  # уже вітали цього користувача раніше

    try:
        client.chat_postMessage(
            channel=user_id,  # надсилаємо в DM користувачу
            text=f"👋 Привіт, <@{user_id}>! Я бот Global Coffee Connect.\n\n{HELP_TEXT}",
        )
    except Exception as e:
        logging.error(f"Не вдалося надіслати привітання користувачу {user_id}: {e}")
        return

    welcomed_users.add(user_id)
    save_welcomed_users(welcomed_users)


web_app = FastAPI()


@web_app.api_route("/", methods=["GET", "HEAD"])
@web_app.api_route("/health", methods=["GET", "HEAD"])
def health_check():
    return {"status": "ok"}


def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(web_app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    # Запускаємо HTTP-сервер у фоновому потоці, щоб Render задеплоїв Web Service
    threading.Thread(target=run_web_server, daemon=True).start()

    # Запускаємо Slack Socket Mode
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
