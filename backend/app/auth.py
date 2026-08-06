import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

import bcrypt
import psycopg
from fastapi import Cookie, Depends, Header, HTTPException, Response, status

from app.db import get_db

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
    secure=True,
    samesite="none",
    expires=expires_at,
    path="/",
  )


def clear_session_cookie(response: Response) -> None:
  response.delete_cookie(
    key=SESSION_COOKIE_NAME,
    path="/",
    httponly=True,
    secure=True,
    samesite="none",
  )


def get_current_user(
  session_token: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
  authorization: Annotated[str | None, Header()] = None,
  conn: psycopg.Connection = Depends(get_db),
) -> dict:
  # 1. Визначити токен: з Cookie або з заголовка Authorization
  token = session_token

  if not token and authorization:
    if authorization.startswith("Bearer "):
      token = authorization.split(" ")[1]
    else:
      token = authorization

  # 2. Якщо токена немає ніде — 401
  if not token:
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

  # 3. Перевірка токена в БД
  row = conn.execute(
    """
        SELECT users.id, users.email, users.first_name, users.last_name, users.timezone
        FROM sessions
        JOIN users ON users.id = sessions.user_id
        WHERE sessions.token = %s AND sessions.expires_at > now()
        """,
    (token,),
  ).fetchone()

  if row is None:
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired or invalid")

  return row


CurrentUser = Annotated[dict, Depends(get_current_user)]
