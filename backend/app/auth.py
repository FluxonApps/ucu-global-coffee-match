import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

import bcrypt
import psycopg
from fastapi import Cookie, Depends, HTTPException, Response, status

from app.db import get_db
from app.settings import settings

SESSION_COOKIE_NAME = "session_token"
SESSION_TTL = timedelta(days=30)


def hash_password(password: str) -> str:
  return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
  return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_session(conn: psycopg.Connection, user_id: int) -> tuple[str, datetime]:
  token = secrets.token_urlsafe(32)
  expires_at = datetime.now(UTC) + SESSION_TTL
  conn.execute(
    "INSERT INTO sessions (token, user_id, expires_at) VALUES (%s, %s, %s)",
    (token, user_id, expires_at),
  )
  conn.commit()
  return token, expires_at


def set_session_cookie(response: Response, token: str, expires_at: datetime) -> None:
  response.set_cookie(
    key=SESSION_COOKIE_NAME,
    value=token,
    httponly=True,
    secure=settings.cookie_secure,
    samesite="lax",
    expires=expires_at,
    path="/",
  )


def clear_session_cookie(response: Response) -> None:
  response.delete_cookie(SESSION_COOKIE_NAME, path="/")


def get_current_user(
  session_token: Annotated[str | None, Cookie()] = None,
  conn: psycopg.Connection = Depends(get_db),
) -> dict:
  if not session_token:
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

  row = conn.execute(
    """
    SELECT users.id, users.email, users.name, users.team, users.timezone
    FROM sessions
    JOIN users ON users.id = sessions.user_id
    WHERE sessions.token = %s AND sessions.expires_at > now()
    """,
    (session_token,),
  ).fetchone()

  if row is None:
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired or invalid")

  return row


CurrentUser = Annotated[dict, Depends(get_current_user)]
