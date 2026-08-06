from datetime import UTC, datetime, timedelta, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import psycopg
from fastapi import APIRouter, Depends, HTTPException

from app.auth import CurrentUser
from app.db import get_db

router = APIRouter(prefix="/availability", tags=["availability"])

DAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
MIN_OVERLAP = timedelta(minutes=30)
LEGACY_TIMEZONES = {
  "SST (UTC-11)": "Pacific/Pago_Pago",
  "HST (UTC-10)": "Pacific/Honolulu",
  "AKST (UTC-9)": "America/Anchorage",
  "PST (UTC-8)": "America/Los_Angeles",
  "MST (UTC-7)": "America/Denver",
  "CST (UTC-6)": "America/Chicago",
  "EST (UTC-5)": "America/New_York",
  "AST (UTC-4)": "America/Halifax",
  "ART (UTC-3)": "America/Argentina/Buenos_Aires",
  "FNT (UTC-2)": "America/Noronha",
  "AZOT (UTC-1)": "Atlantic/Azores",
  "GMT (UTC+0)": "Etc/GMT",
  "CET (UTC+1)": "Europe/Paris",
  "EET (UTC+2)": "Europe/Helsinki",
  "MSK (UTC+3)": "Europe/Moscow",
  "GST (UTC+4)": "Asia/Dubai",
  "PKT (UTC+5)": "Asia/Karachi",
  "IST (UTC+5:30)": "Asia/Kolkata",
  "BST (UTC+6)": "Asia/Dhaka",
  "ICT (UTC+7)": "Asia/Bangkok",
  "CST-China (UTC+8)": "Asia/Shanghai",
  "JST (UTC+9)": "Asia/Tokyo",
  "AEST (UTC+10)": "Australia/Sydney",
  "NZST (UTC+12)": "Pacific/Auckland",
}


def timezone_from_profile(timezone_name: str | None) -> tzinfo:
  """Resolve IANA timezones and the display labels already stored in profiles."""
  if not timezone_name:
    return UTC
  try:
    return ZoneInfo(LEGACY_TIMEZONES.get(timezone_name, timezone_name))
  except ZoneInfoNotFoundError as exc:
    raise ValueError("Timezone must be a valid IANA timezone or a supported profile timezone") from exc


def validate_timezone(timezone_name: str | None) -> None:
  if timezone_name:
    timezone_from_profile(timezone_name)


def local_slot_to_utc(day: int, hour: int, timezone_name: str | None) -> tuple[datetime, datetime]:
  """Convert a recurring local slot to its next real-world UTC occurrence."""
  zone = timezone_from_profile(timezone_name)
  local_now = datetime.now(zone)
  days_until = (day - local_now.weekday()) % 7
  local_start = (local_now + timedelta(days=days_until)).replace(hour=hour, minute=0, second=0, microsecond=0)
  if local_start <= local_now:
    local_start += timedelta(days=7)
  utc_start = local_start.astimezone(UTC)
  return utc_start, utc_start + timedelta(hours=1)


def format_local_range(utc_start: datetime, utc_end: datetime, timezone_name: str | None) -> str:
  zone = timezone_from_profile(timezone_name)
  local_start, local_end = utc_start.astimezone(zone), utc_end.astimezone(zone)
  if local_start.date() == local_end.date():
    return f"{DAY_NAMES[local_start.weekday()]} {local_start:%H:%M}-{local_end:%H:%M}"
  return f"{DAY_NAMES[local_start.weekday()]} {local_start:%H:%M}-{DAY_NAMES[local_end.weekday()]} {local_end:%H:%M}"


def overlaps_busy_interval(start: datetime, end: datetime, busy_intervals: list[tuple[datetime, datetime]]) -> bool:
  return any(max(start, busy_start) < min(end, busy_end) for busy_start, busy_end in busy_intervals)


def get_common_slots_between_users(user_id: int, colleague_id: int, conn: psycopg.Connection) -> list[dict]:
  """Find manual overlaps, excluding concrete Google Calendar busy intervals."""
  rows = conn.execute("SELECT id, timezone FROM users WHERE id IN (%s, %s)", (user_id, colleague_id)).fetchall()
  timezones = {row["id"]: row["timezone"] for row in rows}
  if user_id not in timezones or colleague_id not in timezones:
    return []

  availability = conn.execute(
    """SELECT user_id, day_of_week, hour_slot FROM user_availability
       WHERE user_id IN (%s, %s) AND available = TRUE""",
    (user_id, colleague_id),
  ).fetchall()
  busy_rows = conn.execute(
    """SELECT user_id, starts_at, ends_at FROM google_calendar_busy_slots
       WHERE user_id IN (%s, %s) AND ends_at > now()""",
    (user_id, colleague_id),
  ).fetchall()
  busy: dict[int, list[tuple[datetime, datetime]]] = {user_id: [], colleague_id: []}
  for row in busy_rows:
    busy[row["user_id"]].append((row["starts_at"], row["ends_at"]))

  intervals: dict[int, list[tuple[datetime, datetime]]] = {user_id: [], colleague_id: []}
  for slot in availability:
    interval = local_slot_to_utc(slot["day_of_week"], slot["hour_slot"], timezones[slot["user_id"]])
    if not overlaps_busy_interval(*interval, busy[slot["user_id"]]):
      intervals[slot["user_id"]].append(interval)

  common: dict[tuple[datetime, datetime], dict] = {}
  for user_start, user_end in intervals[user_id]:
    for colleague_start, colleague_end in intervals[colleague_id]:
      start, end = max(user_start, colleague_start), min(user_end, colleague_end)
      if end - start < MIN_OVERLAP:
        continue
      common[(start, end)] = {
        "utc": f"{DAY_NAMES[start.weekday()]} {start:%H:%M}-{end:%H:%M} UTC",
        "utc_iso": start.isoformat(),
        "user_local": {
          "timezone": timezones[user_id] or "UTC",
          "display": format_local_range(start, end, timezones[user_id]),
        },
        "match_local": {
          "timezone": timezones[colleague_id] or "UTC",
          "display": format_local_range(start, end, timezones[colleague_id]),
        },
        "duration_minutes": int((end - start).total_seconds() // 60),
      }
  return [common[key] for key in sorted(common)]


def get_recommended_time_between_users(user_id: int, colleague_id: int, conn: psycopg.Connection) -> dict | None:
  slots = get_common_slots_between_users(user_id, colleague_id, conn)
  return slots[0] if slots else None


def get_recommended_time_for_group(
  participant_ids: list[int],
  conn: psycopg.Connection,
) -> dict | None:
  """
  Finds the earliest meeting slot that works for every participant.
  Takes into account:
  - manual availability
  - time zones
  - Google Calendar busy events
  """

  if not participant_ids:
    return None

  # -------------------------
  # Load timezones
  # -------------------------
  rows = conn.execute(
    """
        SELECT id, timezone
        FROM users
        WHERE id = ANY(%s)
        """,
    (participant_ids,),
  ).fetchall()

  timezones = {row["id"]: row["timezone"] for row in rows}

  if len(timezones) != len(participant_ids):
    return None

  # -------------------------
  # Manual availability
  # -------------------------
  availability_rows = conn.execute(
    """
        SELECT
            user_id,
            day_of_week,
            hour_slot
        FROM user_availability
        WHERE user_id = ANY(%s)
          AND available = TRUE
        """,
    (participant_ids,),
  ).fetchall()

  # -------------------------
  # Google Calendar busy events
  # -------------------------
  busy_rows = conn.execute(
    """
        SELECT
            user_id,
            starts_at,
            ends_at
        FROM google_calendar_busy_slots
        WHERE user_id = ANY(%s)
          AND ends_at > now()
        """,
    (participant_ids,),
  ).fetchall()

  busy = {user_id: [] for user_id in participant_ids}

  for row in busy_rows:
    busy[row["user_id"]].append((row["starts_at"], row["ends_at"]))

  # -------------------------
  # Convert availability to UTC
  # -------------------------
  user_slots = {user_id: set() for user_id in participant_ids}

  for slot in availability_rows:
    interval = local_slot_to_utc(
      slot["day_of_week"],
      slot["hour_slot"],
      timezones[slot["user_id"]],
    )

    if overlaps_busy_interval(
      interval[0],
      interval[1],
      busy[slot["user_id"]],
    ):
      continue

    user_slots[slot["user_id"]].add(interval)

  # Someone has no free slots
  if any(len(slots) == 0 for slots in user_slots.values()):
    return None

  # -------------------------
  # Find common UTC interval
  # -------------------------
  common_slots = set.intersection(*user_slots.values())

  if not common_slots:
    return None

  start, end = sorted(common_slots)[0]

  # -------------------------
  # Format output
  # -------------------------
  return {
    "utc": f"{DAY_NAMES[start.weekday()]} {start:%H:%M}-{end:%H:%M} UTC",
    "utc_iso": start.isoformat(),
    "participants": [
      {
        "user_id": user_id,
        "timezone": timezones[user_id] or "UTC",
        "display": format_local_range(
          start,
          end,
          timezones[user_id],
        ),
      }
      for user_id in participant_ids
    ],
    "duration_minutes": int((end - start).total_seconds() // 60),
  }


@router.get("/common/{colleague_id}")
def find_common_availability(colleague_id: int, user: CurrentUser, conn: psycopg.Connection = Depends(get_db)):
  if not conn.execute("SELECT 1 FROM users WHERE id = %s", (colleague_id,)).fetchone():
    raise HTTPException(status_code=404, detail="Colleague not found")
  return {"common_slots": get_common_slots_between_users(user["id"], colleague_id, conn)}
