import logging
import os
import traceback
from typing import Literal

import psycopg
from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from app.api.availability import get_recommended_time_between_users
from app.auth import CurrentUser
from app.db import get_db
from app.matching.history import get_past_matches, save_match
from app.matching.similarity import score
from app.services.topics import generate_conversation_topics

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/matches", tags=["matches"])

# Base URL used to resolve absolute image links for Slack Block Kit
BASE_URL = os.environ.get("APP_BASE_URL", "https://coffee-match.pp.ua").rstrip("/")

# Slack Client
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
slack_client = WebClient(token=SLACK_BOT_TOKEN) if SLACK_BOT_TOKEN else None


class MatchCreateRequest(BaseModel):
  match_type: Literal["one_to_one", "group"] = "one_to_one"
  group_size: int | None = Field(default=None, ge=3, le=10)


def send_slack_match_notification(
  recipient_slack_id: str,
  partners_info: list[dict],
  recommended_time: str | None,
  topics: list[str],
  is_group: bool = False,
):
  """Sends detailed match notification to a user via Slack bot."""
  if not slack_client or not recipient_slack_id:
    logger.warning("Slack client is not configured or recipient_slack_id is missing.")
    return

  header_text = "🎉 *Group Coffee Match Found!*" if is_group else "🎉 *New 1-on-1 Coffee Match Found!*"

  blocks = [
    {"type": "section", "text": {"type": "mrkdwn", "text": header_text}},
    {"type": "divider"},
  ]

  partner_names = []

  for partner in partners_info:
    name = f"{partner.get('first_name', '')} {partner.get('last_name', '')}".strip() or "Colleague"
    partner_names.append(name)

    role = partner.get("role_title") or "Not specified"
    dept = partner.get("department") or "Not specified"
    bio = partner.get("bio") or "Not specified"

    interests = partner.get("personal_interests") or []
    interests_str = ", ".join(interests) if interests else "Not specified"

    skills = partner.get("skills") or []
    skills_str = ", ".join(skills) if skills else "Not specified"

    user_text = (
      f"👤 *Partner:* <@{partner['slack_user_id']}> ({name})\n"
      f"💼 *Role:* {role} | *Department:* {dept}\n"
      f"📝 *Bio:* {bio}\n"
      f"🎯 *Interests:* {interests_str}\n"
      f"💡 *Skills:* {skills_str}"
    )

    section_block = {
      "type": "section",
      "text": {"type": "mrkdwn", "text": user_text},
    }

    # Format absolute URL for Slack accessory image
    avatar_url = partner.get("avatar_url")
    if avatar_url:
      if not avatar_url.startswith("http://") and not avatar_url.startswith("https://"):
        if not avatar_url.startswith("/"):
          avatar_url = "/" + avatar_url
        avatar_url = f"{BASE_URL}{avatar_url}"

      if avatar_url.startswith("https://"):
        section_block["accessory"] = {
          "type": "image",
          "image_url": avatar_url,
          "alt_text": name,
        }

    blocks.append(section_block)
    blocks.append({"type": "divider"})

  # Recommended meeting time
  if recommended_time:
    blocks.append(
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": f"⏰ *Recommended Meeting Time:*\n{recommended_time}",
        },
      }
    )

  # Conversation starters
  if topics:
    topics_formatted = "\n".join([f"• {t}" for t in topics])
    blocks.append(
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": f"💬 *Conversation Starters:*\n{topics_formatted}",
        },
      }
    )

  fallback_text = f"New coffee match with {', '.join(partner_names)}! ☕"

  try:
    slack_client.chat_postMessage(
      channel=recipient_slack_id,
      text=fallback_text,
      blocks=blocks,
    )
    logger.info(f"Successfully sent Slack notification to {recipient_slack_id}")
  except SlackApiError as e:
    logger.error(f"Failed to send Slack message to {recipient_slack_id}: {e.response['error']}")
  except Exception as e:
    logger.error(f"Unexpected error sending Slack notification: {e}")


def find_one_to_one_match(conn, user, all_users):
  past_pairs = get_past_matches(conn)
  best_user = None
  best_score = -1

  for candidate in all_users:
    if candidate["id"] == user["id"]:
      continue
    if (user["id"], candidate["id"]) in past_pairs:
      continue

    candidate_score = score(user, candidate)

    if candidate_score > best_score or (
      candidate_score == best_score and best_user is not None and candidate["id"] < best_user["id"]
    ):
      best_score = candidate_score
      best_user = candidate

  return best_user


def find_group_match(conn, user, all_users, group_size: int):
  candidates = []

  for candidate in all_users:
    if candidate["id"] == user["id"]:
      continue
    candidate_score = score(user, candidate)
    candidates.append((candidate_score, candidate))

  candidates.sort(key=lambda x: x[0], reverse=True)

  needed_count = group_size - 1
  if len(candidates) < needed_count:
    return None

  return [item[1] for item in candidates[:needed_count]]


@router.get("/history")
def get_match_history(user: CurrentUser, conn: psycopg.Connection = Depends(get_db)):
  """Returns match history for the current authenticated user."""
  rows = conn.execute(
    """
        SELECT
          m.id,
          m.match_type,
          m.matched_at,
          m.conversation_topics,
          colleague.id AS colleague_id,
          colleague.email AS colleague_email,
          colleague.first_name AS colleague_first_name,
          colleague.last_name AS colleague_last_name,
          colleague.avatar_url AS colleague_avatar_url,
          colleague.role_title AS colleague_role_title,
          colleague.department AS colleague_department
        FROM matches m
        JOIN match_participants mp_me
          ON mp_me.match_id = m.id AND mp_me.user_id = %s
        JOIN match_participants mp_other
          ON mp_other.match_id = m.id AND mp_other.user_id != %s
        JOIN users colleague ON colleague.id = mp_other.user_id
        ORDER BY m.matched_at DESC
        """,
    (user["id"], user["id"]),
  ).fetchall()

  return [
    {
      "id": row["id"],
      "match_type": row["match_type"],
      "matched_at": row["matched_at"],
      "recommended_time": get_recommended_time_between_users(user["id"], row["colleague_id"], conn),
      "conversation_topics": row["conversation_topics"] or [],
      "colleague": {
        "id": row["colleague_id"],
        "email": row["colleague_email"],
        "first_name": row["colleague_first_name"],
        "last_name": row["colleague_last_name"],
        "avatar_url": row["colleague_avatar_url"],
        "role_title": row["colleague_role_title"],
        "department": row["colleague_department"],
      },
    }
    for row in rows
  ]


@router.post("/create")
def create_match(
  user: CurrentUser,
  conn: psycopg.Connection = Depends(get_db),
  body: MatchCreateRequest = Body(default_factory=MatchCreateRequest),
):
  try:
    db_user = conn.execute(
      "SELECT * FROM users WHERE id = %s",
      (user["id"],),
    ).fetchone()

    if db_user is None:
      raise HTTPException(
        status_code=404,
        detail="User not found",
      )

    if db_user["slack_user_id"] is None:
      raise HTTPException(
        status_code=409,
        detail="Link your Slack account before creating a match",
      )

    # Retrieve available registered users with connected Slack IDs
    all_users = conn.execute(
      """
            SELECT *
            FROM users
            WHERE slack_user_id IS NOT NULL
              AND is_available = true
            """
    ).fetchall()

    if body.match_type == "one_to_one":
      matched_user = find_one_to_one_match(
        conn,
        db_user,
        all_users,
      )

      if matched_user is None:
        raise HTTPException(
          status_code=409,
          detail="No compatible person is available",
        )

      # 1. Compute recommended time and icebreaker topics
      recommended_time = get_recommended_time_between_users(db_user["id"], matched_user["id"], conn)
      conversation_topics = generate_conversation_topics(db_user, matched_user)

      # 2. Persist match record
      match_id = save_match(
        conn,
        [db_user["id"], matched_user["id"]],
        "one_to_one",
        conversation_topics,
      )

      # 3. Dispatch Slack notifications to both participants
      send_slack_match_notification(
        db_user["slack_user_id"],
        [matched_user],
        recommended_time,
        conversation_topics,
        is_group=False,
      )
      send_slack_match_notification(
        matched_user["slack_user_id"],
        [db_user],
        recommended_time,
        conversation_topics,
        is_group=False,
      )

      return {
        "id": match_id,
        "match_type": "one_to_one",
        "participant_ids": [db_user["id"], matched_user["id"]],
        "recommended_time": recommended_time,
        "conversation_topics": conversation_topics,
        "match": {
          "id": matched_user["id"],
          "first_name": matched_user["first_name"],
          "last_name": matched_user["last_name"],
          "email": matched_user["email"],
          "timezone": matched_user["timezone"],
          "avatar_url": matched_user.get("avatar_url"),
        },
        "match_record": {
          "user1_id": db_user["id"],
          "user2_id": matched_user["id"],
        },
      }

    # Group match logic
    if body.group_size is None:
      raise HTTPException(
        status_code=422,
        detail="group_size is required for a group match",
      )

    group_members = find_group_match(
      conn,
      db_user,
      all_users,
      body.group_size,
    )

    if group_members is None:
      raise HTTPException(
        status_code=409,
        detail=f"Not enough compatible people for a group of {body.group_size}",
      )

    all_participants = [db_user] + group_members
    participant_ids = [m["id"] for m in all_participants]

    # Generate group conversation topics
    conversation_topics = generate_conversation_topics(db_user, group_members[0])

    match_id = save_match(
      conn,
      participant_ids,
      "group",
      conversation_topics,
    )

    # Dispatch notifications to each group member
    for member in all_participants:
      other_partners = [p for p in all_participants if p["id"] != member["id"]]
      send_slack_match_notification(
        member["slack_user_id"],
        other_partners,
        None,
        conversation_topics,
        is_group=True,
      )

    return {
      "id": match_id,
      "match_type": "group",
      "participant_ids": participant_ids,
      "conversation_topics": conversation_topics,
    }

  except HTTPException:
    raise
  except Exception as e:
    traceback.print_exc()
    raise HTTPException(status_code=500, detail=str(e))
