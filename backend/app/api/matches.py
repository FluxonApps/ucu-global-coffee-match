import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db import get_db
from app.matching.history import get_past_matches, save_matches

router = APIRouter(prefix="/matches", tags=["matches"])


def find_match(user, all_users, conn):
    matched_user = all_users[0]

    return matched_user


def store_match(user, best_user, conn):
    """Saves new pair in DB trough history.save_matches."""
    save_matches(conn, [(user["id"], best_user["id"])])
    return {"user1_id": user["id"], "user2_id": best_user["id"]}


class MatchCreateRequest(BaseModel):
    user_id: int


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
