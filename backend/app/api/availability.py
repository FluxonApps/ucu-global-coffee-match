import re
from datetime import datetime, timedelta

import psycopg
from fastapi import APIRouter, Depends, HTTPException

from app.auth import CurrentUser
from app.db import get_db

router = APIRouter(prefix="/availability", tags=["availability"])

# The calendar stores a recurring weekly schedule. This reference Monday only
# gives each weekday a stable date while converting local time to UTC.
REFERENCE_MONDAY = datetime(2026, 1, 5)
DAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def parse_utc_offset(timezone: str | None) -> timedelta:
    """Parse profile values such as ``EET (UTC+2)`` and ``IST (UTC+5:30)``."""
    if not timezone:
        return timedelta()

    match = re.search(r"UTC([+-])(\d{1,2})(?::(\d{2}))?", timezone)
    if not match:
        return timedelta()

    sign, hours, minutes = match.groups()
    offset = timedelta(hours=int(hours), minutes=int(minutes or 0))
    return -offset if sign == "-" else offset


def utc_to_local(utc_start: datetime, timezone: str | None) -> datetime:
    return utc_start + parse_utc_offset(timezone)


def format_local_time(utc_start: datetime, timezone: str | None) -> str:
    local_start = utc_to_local(utc_start, timezone)
    return f"{DAY_NAMES[local_start.weekday()]} {local_start:%H:%M}"


def local_slot_to_utc(day: int, hour: int, timezone: str | None) -> tuple[datetime, datetime]:
    local_start = REFERENCE_MONDAY + timedelta(days=day, hours=hour)
    utc_start = local_start - parse_utc_offset(timezone)

    # Keep UTC dates in the same recurring week even for UTC- and UTC+ offsets.
    while utc_start < REFERENCE_MONDAY:
        utc_start += timedelta(days=7)
    while utc_start >= REFERENCE_MONDAY + timedelta(days=7):
        utc_start -= timedelta(days=7)

    return utc_start, utc_start + timedelta(hours=1)


def get_common_slots_between_users(
    user_id: int, colleague_id: int, conn: psycopg.Connection
) -> list[dict]:
    """Return one-hour overlaps, represented in UTC and in both users' local times."""
    rows = conn.execute(
        "SELECT id, timezone FROM users WHERE id IN (%s, %s)", (user_id, colleague_id)
    ).fetchall()
    timezones = {row["id"]: row["timezone"] for row in rows}
    if user_id not in timezones or colleague_id not in timezones:
        return []

    availability = conn.execute(
        """
        SELECT user_id, day_of_week, hour_slot
        FROM user_availability
        WHERE user_id IN (%s, %s) AND available = TRUE
        """,
        (user_id, colleague_id),
    ).fetchall()

    intervals: dict[int, list[tuple[datetime, datetime]]] = {user_id: [], colleague_id: []}
    for slot in availability:
        intervals[slot["user_id"]].append(
            local_slot_to_utc(slot["day_of_week"], slot["hour_slot"], timezones[slot["user_id"]])
        )

    common: dict[datetime, dict] = {}
    for user_start, user_end in intervals[user_id]:
        for colleague_start, colleague_end in intervals[colleague_id]:
            start, end = max(user_start, colleague_start), min(user_end, colleague_end)
            if end - start < timedelta(hours=1):
                continue

            common[start] = {
                "utc": f"{DAY_NAMES[start.weekday()]} {start:%H:%M} UTC",
                "user_local": {
                    "timezone": timezones[user_id] or "UTC",
                    "display": format_local_time(start, timezones[user_id]),
                },
                "match_local": {
                    "timezone": timezones[colleague_id] or "UTC",
                    "display": format_local_time(start, timezones[colleague_id]),
                },
                "duration_minutes": 60,
            }

    return [common[start] for start in sorted(common)]


def get_recommended_time_between_users(
    user_id: int, colleague_id: int, conn: psycopg.Connection
) -> dict | None:
    slots = get_common_slots_between_users(user_id, colleague_id, conn)
    return slots[0] if slots else None


@router.get("/common/{colleague_id}")
def find_common_availability(
    colleague_id: int,
    user: CurrentUser,
    conn: psycopg.Connection = Depends(get_db),
):
    if not conn.execute("SELECT 1 FROM users WHERE id = %s", (colleague_id,)).fetchone():
        raise HTTPException(status_code=404, detail="Colleague not found")

    return {"common_slots": get_common_slots_between_users(user["id"], colleague_id, conn)}
