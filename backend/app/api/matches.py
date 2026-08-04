import psycopg
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db import get_db

router = APIRouter(prefix="/matches", tags=["matches"])


def find_match(user, all_users):
  matched_user = all_users[0]

  return matched_user


def store_match(user, best_user, conn):
  match = None  # conn.exec # store the match to the matches table of the database.

  return match


class MatchCreateRequest(BaseModel):
  user_id: int


@router.post("/create")
def create_match(body: MatchCreateRequest, conn: psycopg.Connection = Depends(get_db)):
  user_id = body.user_id
  all_users = [None]  # conn.exec("SELECT * from users") # fetch all users
  user = None  # extract the needed user from all_users by user_id

  best_user = find_match(user, all_users)

  match = store_match(user, best_user, conn)  # saved match form the database

  return {"match": match}
