import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth import CurrentUser
from app.db import get_db

router = APIRouter(prefix="/users", tags=["users"])


class UpdateProfileRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    role_title: str | None = None
    department: str | None = None
    timezone: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    slack_user_id: str | None = None
    personal_interests: list[str] | None = None
    skills: list[str] | None = None
    languages: list[str] | None = None


class AvailabilitySlot(BaseModel):
    day: int = Field(ge=0, le=6)
    hour: int = Field(ge=0)
    available: bool


ARRAY_FIELDS = {
    "personal_interests",
    "skills",
    "languages",
}

# Columns safe to return to the client. Deliberately excludes password_hash.
PROFILE_COLUMNS = """
    id, email, first_name, last_name, role_title, department,
    timezone, bio, avatar_url, slack_user_id,
    personal_interests, skills, languages, created_at
"""


@router.get("/me")
def get_profile(
    user: CurrentUser,
    conn: psycopg.Connection = Depends(get_db),
):
    row = conn.execute(
        f"""
        SELECT {PROFILE_COLUMNS}
        FROM users
        WHERE id = %s
        """,
        (user["id"],),
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="User not found")

    return row


@router.patch("/me")
def update_profile(
    body: UpdateProfileRequest,
    user: CurrentUser,
    conn: psycopg.Connection = Depends(get_db),
):
    fields = body.model_dump(exclude_unset=True)
    if not fields:
        return user

    # Array columns are NOT NULL DEFAULT '{}' in the schema — never send NULL for them.
    for key in ARRAY_FIELDS:
        if key in fields and fields[key] is None:
            fields[key] = []

    set_expressions = []
    for key in fields:
        if key in ARRAY_FIELDS:
            set_expressions.append(f"{key} = %s::text[]")
        else:
            set_expressions.append(f"{key} = %s")

    set_clause = ", ".join(set_expressions)

    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        row = cur.execute(
            f"""UPDATE users SET {set_clause}
                WHERE id = %s
                RETURNING {PROFILE_COLUMNS}""",
            (*fields.values(), user["id"]),
        ).fetchone()

    conn.commit()
    return row


@router.get("/me/availability")
def get_availability(
    user: CurrentUser, conn: psycopg.Connection = Depends(get_db)
):
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        rows = cur.execute(
            "SELECT day_of_week, hour_slot, available FROM user_availability WHERE user_id = %s",
            (user["id"],),
        ).fetchall()
    return rows


@router.put("/me/availability")
def set_availability(
    slots: list[AvailabilitySlot],
    user: CurrentUser,
    conn: psycopg.Connection = Depends(get_db),
):
    conn.execute(
        "DELETE FROM user_availability WHERE user_id = %s", (user["id"],)
    )
    conn.executemany(
        """INSERT INTO user_availability (user_id, day_of_week, hour_slot, available)
           VALUES (%s, %s, %s, %s)""",
        [(user["id"], s.day, s.hour, s.available) for s in slots],
    )
    conn.commit()
    return {"status": "ok"}


@router.get("/{user_id}")
def get_user_profile(user_id: int, conn: psycopg.Connection = Depends(get_db)):
    row = conn.execute(
        """
        SELECT id, first_name, last_name, email, avatar_url,
               role_title, department, timezone, bio,
               personal_interests, skills, languages
        FROM users
        WHERE id = %s
        """,
        (user_id,),
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="User not found")

    return row
