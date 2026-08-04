import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db import get_db
from app.matching.history import get_past_matches, save_matches

from app.matching.similarity import score

from app.auth import CurrentUser


router = APIRouter(prefix="/matches", tags=["matches"])

# backend/app/api/matches.py

def find_match(conn, user, all_users):
    past_pairs = get_past_matches(conn)

    best_user = None
    best_score = -1

    for candidate in all_users:
        if candidate["id"] == user["id"]:
            continue

        # history contains both (A, B) and (B, A)
        if (user["id"], candidate["id"]) in past_pairs:
            continue

        candidate_score = score(user, candidate)

        # smallest ID makes ties deterministic
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
    """Saves new pair in DB trough history.save_matches."""

    save_matches(conn, [(user["id"], best_user["id"])])
    return {"user1_id": user["id"], "user2_id": best_user["id"]}


@router.post("/create")
def create_match(
    user: CurrentUser,
    conn: psycopg.Connection = Depends(get_db),
):
    all_users = conn.execute("SELECT * FROM users").fetchall()

    db_user = next((item for item in all_users if item["id"] == user["id"]), None)

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    best_user = find_match(conn, db_user, all_users)

    if best_user is None:
        raise HTTPException(status_code=409, detail="No available match found")

    return {"match": store_match(db_user, best_user, conn)}
