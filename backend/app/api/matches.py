import psycopg
from fastapi import APIRouter, Depends, HTTPException

from app.api.availability import get_recommended_time_between_users
from app.auth import CurrentUser
from app.db import get_db
from app.matching.history import get_past_matches, save_matches
from app.matching.similarity import score
from app.services.topics import generate_conversation_topics
from psycopg.types.json import Jsonb

router = APIRouter(prefix="/matches", tags=["matches"])


def find_match(conn, user, all_users):
    past_pairs = get_past_matches(conn)

    best_user = None
    best_score = -1

    for candidate in all_users:
        if candidate["id"] == user["id"]:
            continue
        if (user["id"], candidate["id"]) in past_pairs:
            continue

        candidate_score = score(user, candidate)

        if (
            candidate_score > best_score
            or (
                candidate_score == best_score
                and best_user is not None
                and candidate["id"] < best_user["id"]
            )
        ):
            best_score = candidate_score
            best_user = candidate

    return best_user


def store_match(user, best_user, conn):
    """Saves new pair in DB through history.save_matches."""
    save_matches(conn, [(user["id"], best_user["id"])])

    return {
        "user1_id": user["id"],
        "user2_id": best_user["id"],
    }


@router.get("/history")
def get_match_history(user: CurrentUser, conn: psycopg.Connection = Depends(get_db)):
    """Return the current user's recorded matches with the matched colleague's details."""
    rows = conn.execute(
        """
        SELECT
          matches.id,
          matches.matched_at,
          matches.conversation_topics,
          colleague.id AS colleague_id,
          colleague.email AS colleague_email,
          colleague.first_name AS colleague_first_name,
          colleague.last_name AS colleague_last_name,
          colleague.avatar_url AS colleague_avatar_url
        FROM matches
        JOIN users AS colleague
          ON colleague.id = CASE
            WHEN matches.user1_id = %s THEN matches.user2_id
            ELSE matches.user1_id
          END
        WHERE matches.user1_id = %s OR matches.user2_id = %s
        ORDER BY matches.matched_at DESC
        """,
        (user["id"], user["id"], user["id"]),
    ).fetchall()

    return [
        {
            "id": row["id"],
            "matched_at": row["matched_at"],
            "recommended_time": get_recommended_time_between_users(user["id"], row["colleague_id"], conn),
            "conversation_topics": row["conversation_topics"] or [],
            "colleague": {
                "id": row["colleague_id"],
                "email": row["colleague_email"],
                "first_name": row["colleague_first_name"],
                "last_name": row["colleague_last_name"],
                "avatar_url": row["colleague_avatar_url"],
            },
        }
        for row in rows
    ]


@router.post("/create")
def create_match(
    user: CurrentUser,
    conn: psycopg.Connection = Depends(get_db),
):
    all_users = conn.execute("SELECT * FROM users").fetchall()

    db_user = next(
        (item for item in all_users if item["id"] == user["id"]),
        None,
    )

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    best_user = find_match(conn, db_user, all_users)

    if best_user is None:
        raise HTTPException(
            status_code=409,
            detail="No available match found",
        )

    recommended_time = get_recommended_time_between_users(db_user["id"], best_user["id"], conn)

    stored_match = store_match(
        db_user,
        best_user,
        conn,
    )

    conversation_topics = generate_conversation_topics(db_user, best_user)

    conn.execute(
        """
        UPDATE matches
        SET conversation_topics = %s
        WHERE (user1_id = %s AND user2_id = %s) OR (user1_id = %s AND user2_id = %s)
        """,
        (
            Jsonb(conversation_topics),
            db_user["id"], best_user["id"],
            best_user["id"], db_user["id"],
        ),
    )
    conn.commit()

    return {
        "match": {
            "id": best_user["id"],
            "first_name": best_user["first_name"],
            "last_name": best_user["last_name"],
            "email": best_user["email"],
            "timezone": best_user["timezone"],
            "avatar_url": best_user.get("avatar_url"),
        },
        "match_record": stored_match,
        "recommended_time": recommended_time,
        "conversation_topics": conversation_topics,
    }
