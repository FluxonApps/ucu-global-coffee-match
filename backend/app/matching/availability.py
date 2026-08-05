from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


COFFEE_DURATION_HOURS = 1
UTC = ZoneInfo("UTC")


def get_timezone(timezone_name: str | None) -> ZoneInfo:
    if not timezone_name:
        return UTC

    try:
        return ZoneInfo(timezone_name)
    except Exception:
        return UTC


def get_weekday_slots(
    availability: list[dict],
    timezone_name: str | None,
) -> set[tuple[int, int]]:
    """
    Convert user's local availability slots to UTC.

    day:
        0 = Monday
        6 = Sunday

    hour:
        local starting hour of the available one-hour slot.
    """

    timezone = get_timezone(timezone_name)

    result: set[tuple[int, int]] = set()

    # Monday used only as a reference date.
    reference_monday = datetime(
        2026,
        1,
        5,
        0,
        0,
        tzinfo=timezone,
    )

    for slot in availability:
        if not slot.get("available"):
            continue

        day = slot["day"]
        hour = slot["hour"]

        # IMPORTANT:
        # The availability hour belongs to the user's LOCAL timezone.
        local_dt = reference_monday + timedelta(days=day, hours=hour)

        # Convert the local time to UTC.
        utc_dt = local_dt.astimezone(UTC)

        result.add(
            (
                utc_dt.weekday(),
                utc_dt.hour,
            )
        )

    return result


def find_recommended_time(
    availability_a: list[dict],
    timezone_a: str | None,
    availability_b: list[dict],
    timezone_b: str | None,
) -> dict | None:
    """
    Find a one-hour slot available for both users.

    Availability is entered in each user's local timezone.
    Matching is performed in UTC.

    Returns:
        UTC time,
        user's local time,
        matched user's local time.
    """

    slots_a = get_weekday_slots(
        availability_a,
        timezone_a,
    )

    slots_b = get_weekday_slots(
        availability_b,
        timezone_b,
    )

    common_slots = slots_a & slots_b

    if not common_slots:
        return None

    def score(slot: tuple[int, int]) -> int:
        """
        Prefer reasonable daytime hours in UTC.
        """

        _, hour = slot

        if 9 <= hour < 17:
            return 3

        if 17 <= hour < 20:
            return 2

        if 8 <= hour < 9 or 20 <= hour < 21:
            return 1

        return 0

    best_day, best_hour = max(
        common_slots,
        key=lambda slot: (
            score(slot),
            -slot[0],
            -slot[1],
        ),
    )

    recommended_utc = datetime(
        2026,
        1,
        5,
        best_hour,
        0,
        tzinfo=UTC,
    ) + timedelta(days=best_day)

    user_a_local = recommended_utc.astimezone(
        get_timezone(timezone_a)
    )

    user_b_local = recommended_utc.astimezone(
        get_timezone(timezone_b)
    )

    return {
        "utc": recommended_utc.isoformat(),
        "duration_hours": COFFEE_DURATION_HOURS,
        "user_local": user_a_local.isoformat(),
        "match_local": user_b_local.isoformat(),
    }