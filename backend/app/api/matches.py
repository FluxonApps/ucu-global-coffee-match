import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db import get_db
from app.matching.history import get_past_matches, save_matches

from app.matching.similarity import score

router = APIRouter(prefix="/matches", tags=["matches"])

# backend/app/api/matches.py

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
    save_matches(conn, [(user["id"], best_user["id"])])
    return {"user1_id": user["id"], "user2_id": best_user["id"]}


class MatchCreateRequest(BaseModel):
    user_id: int


@router.post("/create")
def create_match(body: MatchCreateRequest, conn: psycopg.Connection = Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users;")
        all_users = cur.fetchall()

    user = next((u for u in all_users if u["id"] == body.user_id), None)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    best_user = find_match(conn, user, all_users)

    if best_user is None:
        raise HTTPException(
            status_code=409,
            detail="No available match found for this user",
        )

    match = store_match(user, best_user, conn)
    return {"match": match}
