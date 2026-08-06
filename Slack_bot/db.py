import logging
import os
import random
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Fetch database URL and fix PostgreSQL prefix for Render deployment if needed
DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


@contextmanager
def get_connection():
    """Context manager for database connection — ensures proper closure."""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set")
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


def get_registered_users(exclude_slack_id: str | None = None) -> list[dict]:
    """
    Returns a list of all registered users who linked their Slack account
    (slack_user_id IS NOT NULL) and are available.
    """
    query = """
        SELECT id, first_name, last_name, email, avatar_url,
               role_title, department, slack_user_id,
               personal_interests, bio, skills, languages
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
    """Returns a single user by their slack_user_id (or None if not found)."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM users WHERE slack_user_id = %s",
                (slack_user_id,),
            )
            return cur.fetchone()


def record_match(user1_db_id: int, user2_db_id: int, conversation_topics: list[str] | None = None) -> int:
    """Records a new match in the matches table and adds participants to match_participants."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO matches (match_type, status, conversation_topics, matched_at)
                VALUES ('one_to_one', 'created', %s, NOW())
                RETURNING id;
                """,
                (conversation_topics or [],),
            )
            match_id = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO match_participants (match_id, user_id)
                VALUES (%s, %s), (%s, %s);
                """,
                (match_id, user1_db_id, match_id, user2_db_id),
            )
        conn.commit()
        return match_id


def link_slack_account(user_id: int, slack_user_id: str) -> None:
    """Links Slack account to user by setting their slack_user_id."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET slack_user_id = %s WHERE id = %s",
                (slack_user_id, user_id),
            )
        conn.commit()


def get_user_by_code(code: str) -> dict | None:
    """Returns a user by their registration code (verification_code) or None."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM users WHERE verification_code = %s",
                (code,),
            )
            return cur.fetchone()


def set_availability(slack_user_id: str, is_available: bool) -> None:
    """Enables/disables user availability for matching (used by /mute and /unmute commands)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET is_available = %s WHERE slack_user_id = %s",
                (is_available, slack_user_id),
            )
        conn.commit()


def get_last_match_partner_id(user_db_id: int) -> int | None:
    """Returns the user ID of the last partner the user was matched with."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
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
            return row["user_id"] if row else None


def find_best_match_for_user(requester_id: int) -> dict | None:
    """Finds the best matching user based on shared interests, skills, and languages."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # 1. Get requester profile details
            cur.execute(
                """
                SELECT id, personal_interests, skills, languages
                FROM users
                WHERE id = %s
                """,
                (requester_id,),
            )
            req_user = cur.fetchone()
            if not req_user:
                return None

            req_interests = set(req_user.get("personal_interests") or [])
            req_skills = set(req_user.get("skills") or [])
            req_languages = set(req_user.get("languages") or [])

            # Get the ID of the previous match partner to avoid consecutive matching
            last_partner_id = get_last_match_partner_id(requester_id)

            # 2. Retrieve all available candidate users with linked Slack IDs
            cur.execute(
                """
                SELECT id, first_name, last_name, slack_user_id, personal_interests,
                       skills, languages, bio, role_title, department
                FROM users
                WHERE is_available = true
                  AND slack_user_id IS NOT NULL
                  AND id != %s
                  AND (%s::int IS NULL OR id != %s)
                """,
                (requester_id, last_partner_id, last_partner_id),
            )
            candidates = cur.fetchall()

            if not candidates:
                return None

            # 3. Calculate match score for each candidate
            scored_candidates = []
            for cand in candidates:
                cand_interests = set(cand.get("personal_interests") or [])
                cand_skills = set(cand.get("skills") or [])
                cand_languages = set(cand.get("languages") or [])

                shared_interests = req_interests.intersection(cand_interests)
                shared_skills = req_skills.intersection(cand_skills)
                shared_languages = req_languages.intersection(cand_languages)

                # Similarity scoring algorithm
                score = (
                    (len(shared_interests) * 3)
                    + (len(shared_skills) * 2)
                    + (len(shared_languages) * 1)
                )

                scored_candidates.append(
                    {
                        "candidate": dict(cand),
                        "score": score,
                        "shared_interests": list(shared_interests),
                        "shared_skills": list(shared_skills),
                    }
                )

            # Sort candidates by score descending
            scored_candidates.sort(key=lambda x: x["score"], reverse=True)

            top_score = scored_candidates[0]["score"]
            top_candidates = [c for c in scored_candidates if c["score"] == top_score]

            return random.choice(top_candidates)


def create_smart_match(
    user1_id: int, user2_id: int, conversation_topics: list[str]
) -> int:
    """Creates a match record and adds participants to the match_participants table."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO matches (match_type, status, conversation_topics, matched_at)
                VALUES ('one_to_one', 'created', %s, NOW())
                RETURNING id;
                """,
                (conversation_topics,),
            )
            match_id = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO match_participants (match_id, user_id)
                VALUES (%s, %s), (%s, %s);
                """,
                (match_id, user1_id, match_id, user2_id),
            )
            conn.commit()
            return match_id
