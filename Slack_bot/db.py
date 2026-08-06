import logging
import os
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Отримуємо URL та автоматично виправляємо префікс для Render
DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


@contextmanager
def get_connection():
    """Контекстний менеджер для з'єднання з базою — гарантує закриття."""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set")
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
    """Повертає користувача за реєстраційним кодом (verification_code) або None."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM users WHERE verification_code = %s",
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


def get_last_match_partner_id(user_db_id: int):
    """Повертає ID останнього партнера, з яким був зметчений користувач."""
    with get_connection() as conn:  # або ваш спосіб отримання коннекту/курсора
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT mp_partner.user_id
                FROM matches m
                JOIN match_participants mp ON m.id = mp.match_id
                JOIN match_participants mp_partner
                    ON m.id = mp_partner.match_id
                   AND mp_partner.user_id != %s
                WHERE mp.user_id = %s
                ORDER BY m.matched_at DESC
                LIMIT 1;
            """,
                (user_db_id, user_db_id),
            )
            row = cur.fetchone()
            if row:
                return row[0]  # або row["user_id"], залежно від типу курсора
            return None
