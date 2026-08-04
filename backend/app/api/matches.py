import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import CurrentUser
from app.db import get_db
from app.matching.history import get_past_matches, save_matches

from app.matching.history import get_past_matches, save_matches
from app.matching.similarity import score

router = APIRouter(prefix="/matches", tags=["matches"])

# backend/app/api/matches.py

def find_match(user, all_users, conn):
    matched_user = all_users[0]

    return matched_user

    for candidate in all_users:
        if candidate["id"] == user["id"]:
            continue

def store_match(user, best_user, conn):
    """Saves new pair in DB trough history.save_matches."""
    save_matches(conn, [(user["id"], best_user["id"])])
    return {"user1_id": user["id"], "user2_id": best_user["id"]}


class MatchCreateRequest(BaseModel):
    user_id: int


@router.get("/history")
def get_match_history(user: CurrentUser, conn: psycopg.Connection = Depends(get_db)):
    """Return the current user's recorded matches with the matched colleague's details."""
    rows = conn.execute(
        """
        SELECT
          matches.id,
          matches.matched_at,
          colleague.id AS colleague_id,
          colleague.email AS colleague_email,
          colleague.first_name AS colleague_first_name,
          colleague.last_name AS colleague_last_name
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
            "colleague": {
                "id": row["colleague_id"],
                "email": row["colleague_email"],
                "first_name": row["colleague_first_name"],
                "last_name": row["colleague_last_name"],
            },
        }
        for row in rows
    ]


@router.post("/create")
def create_match(body: MatchCreateRequest, conn: psycopg.Connection = Depends(get_db)):
    user_id = body.user_id

    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users;")
        all_users = cur.fetchall()
    
    user = next((u for u in all_users if u["id"] == user_id), None)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    candidates = [u for u in all_users if u["id"] != user_id]
    best_user = find_match(user, candidates, conn)

    if best_user is None:
        raise HTTPException(status_code=409, detail="No available match found for this user")

    match = store_match(user, best_user, conn)  # saved match form the database

    return {"match": match}
