import json
import secrets
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import psycopg
from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from app.auth import CurrentUser
from app.db import get_db
from app.settings import settings

router = APIRouter(prefix="/users/me/calendar", tags=["google-calendar"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_FREEBUSY_URL = "https://www.googleapis.com/calendar/v3/freeBusy"
CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar.events"


def require_google_config() -> tuple[str, str, Fernet]:
  if not settings.google_client_id or not settings.google_client_secret or not settings.google_token_encryption_key:
    raise HTTPException(status_code=503, detail="Google Calendar is not configured on this server")
  try:
    cipher = Fernet(settings.google_token_encryption_key.encode())
  except (TypeError, ValueError) as exc:
    raise HTTPException(status_code=503, detail="GOOGLE_TOKEN_ENCRYPTION_KEY is invalid") from exc
  return settings.google_client_id, settings.google_client_secret, cipher


def encrypt_token(token: str) -> str:
  return require_google_config()[2].encrypt(token.encode()).decode()


def decrypt_token(token: str) -> str:
  try:
    return require_google_config()[2].decrypt(token.encode()).decode()
  except InvalidToken as exc:
    raise HTTPException(status_code=409, detail="Google Calendar token is invalid; reconnect it") from exc


def post_form(url: str, fields: dict[str, str]) -> dict:
  request = Request(url, data=urlencode(fields).encode(), headers={"Content-Type": "application/x-www-form-urlencoded"})
  try:
    with urlopen(request, timeout=15) as response:
      return json.loads(response.read())
  except HTTPError as exc:
    body = exc.read().decode(errors="replace")
    if "invalid_grant" in body:
      raise HTTPException(status_code=409, detail="Google authorization expired; reconnect Calendar") from exc
    raise HTTPException(status_code=502, detail="Google token request failed") from exc


def google_post(url: str, payload: dict, access_token: str) -> dict:
  request = Request(
    url,
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"},
    method="POST",
  )
  try:
    with urlopen(request, timeout=15) as response:
      return json.loads(response.read())
  except HTTPError as exc:
    if exc.code in {401, 403}:
      raise HTTPException(status_code=409, detail="Google Calendar authorization failed; reconnect it") from exc
    raise HTTPException(status_code=502, detail="Google Calendar request failed") from exc


def disconnect_user_calendar(user_id: int, conn: psycopg.Connection) -> None:
  conn.execute("DELETE FROM google_calendar_tokens WHERE user_id = %s", (user_id,))
  conn.execute("DELETE FROM google_calendar_busy_slots WHERE user_id = %s", (user_id,))
  conn.commit()


def get_access_token(user_id: int, conn: psycopg.Connection) -> str:
  token = conn.execute(
    """SELECT access_token_encrypted, refresh_token_encrypted, expires_at
       FROM google_calendar_tokens WHERE user_id = %s""",
    (user_id,),
  ).fetchone()
  if token is None:
    raise HTTPException(status_code=409, detail="Connect Google Calendar first")
  if token["expires_at"] is None or token["expires_at"] > datetime.now(UTC) + timedelta(minutes=1):
    return decrypt_token(token["access_token_encrypted"])
  if not token["refresh_token_encrypted"]:
    disconnect_user_calendar(user_id, conn)
    raise HTTPException(status_code=409, detail="Google authorization expired; reconnect Calendar")

  client_id, client_secret, _ = require_google_config()
  try:
    refreshed = post_form(
      GOOGLE_TOKEN_URL,
      {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": decrypt_token(token["refresh_token_encrypted"]),
        "grant_type": "refresh_token",
      },
    )
  except HTTPException as exc:
    if exc.status_code == 409:
      disconnect_user_calendar(user_id, conn)
    raise
  expires_at = datetime.now(UTC) + timedelta(seconds=int(refreshed.get("expires_in", 3600)))
  conn.execute(
    """UPDATE google_calendar_tokens SET access_token_encrypted = %s, expires_at = %s, updated_at = now()
       WHERE user_id = %s""",
    (encrypt_token(refreshed["access_token"]), expires_at, user_id),
  )
  conn.commit()
  return refreshed["access_token"]


def sync_busy_intervals(user_id: int, conn: psycopg.Connection) -> int:
  now = datetime.now(UTC)
  try:
    access_token = get_access_token(user_id, conn)
    response = google_post(
      GOOGLE_FREEBUSY_URL,
      {"timeMin": now.isoformat(), "timeMax": (now + timedelta(days=14)).isoformat(), "items": [{"id": "primary"}]},
      access_token,
    )
  except HTTPException as exc:
    if exc.status_code == 409:
      disconnect_user_calendar(user_id, conn)
    raise
  rows: list[tuple[int, datetime, datetime, str]] = []
  for interval in response.get("calendars", {}).get("primary", {}).get("busy", []):
    try:
      start = datetime.fromisoformat(interval["start"].replace("Z", "+00:00"))
      end = datetime.fromisoformat(interval["end"].replace("Z", "+00:00"))
    except (KeyError, ValueError):
      continue
    if end > start:
      rows.append((user_id, start, end, "Google Calendar busy"))
  with conn.cursor() as cur:
    cur.execute("DELETE FROM google_calendar_busy_slots WHERE user_id = %s", (user_id,))
    cur.executemany(
      """INSERT INTO google_calendar_busy_slots (user_id, starts_at, ends_at, event_summary)
         VALUES (%s, %s, %s, %s)""",
      rows,
    )
  conn.execute("UPDATE google_calendar_tokens SET last_synced_at = now() WHERE user_id = %s", (user_id,))
  conn.commit()
  return len(rows)


@router.get("/status")
def calendar_status(user: CurrentUser, conn: psycopg.Connection = Depends(get_db)):
  token = conn.execute("SELECT last_synced_at FROM google_calendar_tokens WHERE user_id = %s", (user["id"],)).fetchone()
  busy = conn.execute(
    "SELECT count(*) AS count FROM google_calendar_busy_slots WHERE user_id = %s AND ends_at > now()", (user["id"],)
  ).fetchone()
  return {
    "connected": token is not None,
    "last_synced_at": token["last_synced_at"] if token else None,
    "busy_slots": busy["count"],
  }


@router.get("/connect")
def connect_calendar(user: CurrentUser, conn: psycopg.Connection = Depends(get_db)):
  client_id, _, _ = require_google_config()
  state = secrets.token_urlsafe(32)
  conn.execute("DELETE FROM google_oauth_states WHERE expires_at < now() OR user_id = %s", (user["id"],))
  conn.execute(
    "INSERT INTO google_oauth_states (state, user_id, expires_at) VALUES (%s, %s, %s)",
    (state, user["id"], datetime.now(UTC) + timedelta(minutes=10)),
  )
  conn.commit()
  query = urlencode(
    {
      "client_id": client_id,
      "redirect_uri": settings.google_redirect_uri,
      "response_type": "code",
      "scope": CALENDAR_SCOPE,
      "access_type": "offline",
      "prompt": "consent",
      "state": state,
    }
  )
  return RedirectResponse(f"{GOOGLE_AUTH_URL}?{query}")


@router.get("/callback")
def calendar_callback(code: str, state: str, conn: psycopg.Connection = Depends(get_db)):
  state_row = conn.execute(
    "DELETE FROM google_oauth_states WHERE state = %s AND expires_at > now() RETURNING user_id", (state,)
  ).fetchone()
  if state_row is None:
    raise HTTPException(status_code=400, detail="Google authorization state expired; try again")
  client_id, client_secret, _ = require_google_config()
  token = post_form(
    GOOGLE_TOKEN_URL,
    {
      "code": code,
      "client_id": client_id,
      "client_secret": client_secret,
      "redirect_uri": settings.google_redirect_uri,
      "grant_type": "authorization_code",
    },
  )
  expires_at = datetime.now(UTC) + timedelta(seconds=int(token.get("expires_in", 3600)))
  existing = conn.execute(
    "SELECT refresh_token_encrypted FROM google_calendar_tokens WHERE user_id = %s",
    (state_row["user_id"],),
  ).fetchone()
  refresh_token = token.get("refresh_token")
  if not refresh_token and not existing:
    raise HTTPException(status_code=502, detail="Google did not return a refresh token; reconnect Calendar")
  refresh_token_encrypted = encrypt_token(refresh_token) if refresh_token else existing["refresh_token_encrypted"]
  conn.execute(
    """INSERT INTO google_calendar_tokens (user_id, access_token_encrypted, refresh_token_encrypted, expires_at)
       VALUES (%s, %s, %s, %s)
       ON CONFLICT (user_id) DO UPDATE SET access_token_encrypted = EXCLUDED.access_token_encrypted,
         refresh_token_encrypted = EXCLUDED.refresh_token_encrypted,
         expires_at = EXCLUDED.expires_at, updated_at = now()""",
    (state_row["user_id"], encrypt_token(token["access_token"]), refresh_token_encrypted, expires_at),
  )
  conn.commit()
  with suppress(HTTPException):
    sync_busy_intervals(state_row["user_id"], conn)
  return RedirectResponse(f"{settings.frontend_url}/profile?calendar=connected")


@router.post("/sync")
def sync_calendar(user: CurrentUser, conn: psycopg.Connection = Depends(get_db)):
  return {"busy_slots": sync_busy_intervals(user["id"], conn), "synced_at": datetime.now(UTC)}


@router.delete("")
def disconnect_calendar(user: CurrentUser, conn: psycopg.Connection = Depends(get_db)):
  disconnect_user_calendar(user["id"], conn)
  return {"status": "disconnected"}
