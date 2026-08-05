import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import CurrentUser
from app.db import get_db

router = APIRouter(prefix="/users", tags=["users"])


class UpdateProfileRequest(BaseModel):
  first_name: str | None = None
  last_name: str | None = None
  timezone: str | None = None


@router.get("/me")
def get_profile(user: CurrentUser):
  return user


@router.patch("/me")
def update_profile(
  body: UpdateProfileRequest,
  user: CurrentUser,
  conn: psycopg.Connection = Depends(get_db),
):
  fields = body.model_dump(exclude_unset=True)
  if not fields:
    return user

  set_clause = ", ".join(f"{key} = %s" for key in fields)
  row = conn.execute(
    f"UPDATE users SET {set_clause} WHERE id = %s RETURNING id, email, first_name, last_name, timezone",
    (*fields.values(), user["id"]),
  ).fetchone()
  conn.commit()

  return row

from fastapi import HTTPException

@router.get("/{user_id}")
def get_user_profile(user_id: int, conn: psycopg.Connection = Depends(get_db)):
    row = conn.execute(
        """
        SELECT id, first_name, last_name, email, avatar_url,
               role_title, department, timezone, bio,
               personal_interests, conversation_topics, skills, languages
        FROM users
        WHERE id = %s
        """,
        (user_id,),
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="User not found")

    return row