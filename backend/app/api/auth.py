import secrets
import string

import psycopg
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field

from app.auth import (
  CurrentUser,
  clear_session_cookie,
  create_session,
  hash_password,
  set_session_cookie,
  verify_password,
)
from app.db import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


def generate_unique_user_code(conn: psycopg.Connection) -> str:
  alphabet = string.ascii_letters + string.digits
  while True:
    code = "".join(secrets.choice(alphabet) for _ in range(16))
    exists = conn.execute("SELECT 1 FROM users WHERE verification_code = %s", (code,)).fetchone()
    if not exists:
      return code


class RegisterRequest(BaseModel):
  email: EmailStr
  password: str
  first_name: str = Field(min_length=1, pattern=r".*\S.*")
  last_name: str = Field(min_length=1, pattern=r".*\S.*")


class LoginRequest(BaseModel):
  email: EmailStr
  password: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
  body: RegisterRequest,
  response: Response,
  conn: psycopg.Connection = Depends(get_db),
):
  existing = conn.execute("SELECT id FROM users WHERE email = %s", (body.email,)).fetchone()
  if existing:
    raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

  verification_code = generate_unique_user_code(conn)

  row = conn.execute(
    """
        INSERT INTO users (email, password_hash, first_name, last_name, verification_code)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, email, first_name, last_name, timezone, verification_code
        """,
    (
      body.email,
      hash_password(body.password),
      body.first_name.strip(),
      body.last_name.strip(),
      verification_code,
    ),
  ).fetchone()
  conn.commit()

  token, expires_at = create_session(conn, row["id"])
  set_session_cookie(response, token, expires_at)

  # Конвертуємо результат у словник та повертаємо токен у JSON
  user_data = dict(row)
  user_data["token"] = token
  return user_data


@router.post("/login")
def login(body: LoginRequest, response: Response, conn: psycopg.Connection = Depends(get_db)):
  row = conn.execute(
    "SELECT id, email, password_hash, first_name, last_name, timezone FROM users WHERE email = %s",
    (body.email,),
  ).fetchone()

  if row is None or not verify_password(body.password, row["password_hash"]):
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

  token, expires_at = create_session(conn, row["id"])
  set_session_cookie(response, token, expires_at)

  del row["password_hash"]

  # Конвертуємо результат у словник та повертаємо токен у JSON
  user_data = dict(row)
  user_data["token"] = token
  return user_data


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
  response: Response,
  session_token: str | None = Cookie(default=None),
  conn: psycopg.Connection = Depends(get_db),
):
  if session_token:
    conn.execute("DELETE FROM sessions WHERE token = %s", (session_token,))
    conn.commit()
  clear_session_cookie(response)


@router.get("/me")
def me(user: CurrentUser):
  return user
