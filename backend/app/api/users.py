import psycopg
from fastapi import APIRouter, Depends
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
