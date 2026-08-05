"""
Модуль для роботи з PostgreSQL базою даних бота.

Очікує змінну оточення DATABASE_URL у форматі:
    postgresql://user:password@localhost:5432/slackbot_db

Встановлення залежності:
    pip install psycopg2-binary
"""

import os
import logging
from contextlib import contextmanager
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ["DATABASE_URL"]


@contextmanager
def get_connection():
    """Контекстний менеджер для з'єднання з базою — гарантує закриття."""
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


def get_registered_users(exclude_slack_id: str | None = None) -> list[dict]:
    """
    Повертає список усіх зареєстрованих користувачів, які прив'язали
    свій Slack-акаунт (slack_user_id IS NOT NULL).

    exclude_slack_id — опційно виключити конкретного користувача
    (наприклад, того, хто викликав команду, щоб не вибрало самого себе).
    """
    query = """
        SELECT id, first_name, last_name, email, avatar_url,
               role_title, department, slack_user_id
        FROM users
        WHERE slack_user_id IS NOT NULL
          AND is_available = true
    """
    params: list = []

    if exclude_slack_id:
        query += " AND slack_user_id != %s"
        params.append(exclude_slack_id)

    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            return list(cur.fetchall())


def get_user_by_slack_id(slack_user_id: str) -> dict | None:
    """Повертає одного користувача за його slack_user_id (або None)."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM users WHERE slack_user_id = %s",
                (slack_user_id,),
            )
            return cur.fetchone()


def record_match(user1_db_id: int, user2_db_id: int) -> None:
    """Записує новий метч у таблицю matches."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO matches (user1_id, user2_id, status)
                VALUES (%s, %s, 'created')
                """,
                (user1_db_id, user2_db_id),
            )
        conn.commit()


def link_slack_account(user_id: int, slack_user_id: str) -> None:
    """Прив'язує Slack-акаунт до користувача (записує slack_user_id)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET slack_user_id = %s WHERE id = %s",
                (slack_user_id, user_id),
            )
        conn.commit()


def get_user_by_code(code: str) -> dict | None:
    """Повертає користувача за реєстраційним кодом (code_user) або None."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM users WHERE code_user = %s",
                (code,),
            )
            return cur.fetchone()


def set_availability(slack_user_id: str, is_available: bool) -> None:
    """Вмикає/вимикає участь користувача у вибірці /random_user."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET is_available = %s WHERE slack_user_id = %s",
                (is_available, slack_user_id),
            )
        conn.commit()


def get_last_match_partner_id(user_db_id: int) -> int | None:
    """
    Повертає ID користувача, з яким user_db_id був заматчений
    востаннє (щоб можна було уникати повторів двічі поспіль).
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user1_id, user2_id
                FROM matches
                WHERE user1_id = %s OR user2_id = %s
                ORDER BY matched_at DESC
                LIMIT 1
                """,
                (user_db_id, user_db_id),
            )
            row = cur.fetchone()
            if not row:
                return None
            user1_id, user2_id = row
            return user2_id if user1_id == user_db_id else user1_id
