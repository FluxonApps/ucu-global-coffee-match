import logging
import os
import traceback
from typing import Literal

import psycopg
from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from app.api.availability import (
  get_recommended_time_between_users,
  get_recommended_time_for_group,
)
from app.auth import CurrentUser
from app.db import get_db
from app.matching.history import get_past_matches, save_match
from app.matching.similarity import score
from app.services.topics import (
  generate_conversation_topics,
  generate_group_conversation_topics,
)

logger = logging.getLogger(__name__)
MIN_GROUP_SIZE = 3
MAX_GROUP_SIZE = 7

# Minimum similarity score required between any two members
MIN_GROUP_SIMILARITY = 2
router = APIRouter(prefix="/matches", tags=["matches"])

# Base URL used to resolve absolute image links for Slack Block Kit
BASE_URL = os.environ.get("APP_BASE_URL", "https://coffee-match.pp.ua").rstrip("/")

# Slack Client
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
slack_client = WebClient(token=SLACK_BOT_TOKEN) if SLACK_BOT_TOKEN else None


class MatchCreateRequest(BaseModel):
  match_type: Literal["one_to_one", "group"] = "one_to_one"


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

    label = "Partner" if not is_group else "Group member"

    user_text = (
      f"👤 *{label}:* <@{partner['slack_user_id']}> ({name})\n"
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
    if isinstance(recommended_time, dict):
      lines = [f"*UTC:* {recommended_time['utc']}"]

      if "user_local" in recommended_time:
        lines.append(f"*Your time:* {recommended_time['user_local']['display']}")
        lines.append(f"*Partner's time:* {recommended_time['match_local']['display']}")

      elif "participants" in recommended_time:
        lines.append("")
        lines.append("*Local times:*")

        for participant in recommended_time["participants"]:
          lines.append(f"• {participant['display']} ({participant['timezone']})")

      recommended_time_text = "\n".join(lines)

    else:
      recommended_time_text = str(recommended_time)

    blocks.append(
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": f"⏰ *Recommended Meeting Time:*\n{recommended_time_text}",
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

  fallback_text = (
    f"New group coffee match with {', '.join(partner_names)}! ☕"
    if is_group
    else f"New coffee match with {partner_names[0]}! ☕"
  )

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


def find_group_match(conn, user, all_users):
  past_pairs = get_past_matches(conn)

  # Build a list of candidates sorted by similarity to the initiator
  candidates = []

  for candidate in all_users:
    if candidate["id"] == user["id"]:
      continue

    if (user["id"], candidate["id"]) in past_pairs:
      continue

    candidates.append(
      (
        score(user, candidate),
        candidate,
      )
    )

  candidates.sort(reverse=True, key=lambda x: x[0])

  group = [user]

  for _, candidate in candidates:
    if len(group) >= MAX_GROUP_SIZE:
      break

    compatible = True

    # Candidate must be similar to EVERY existing member
    for member in group:
      if member["id"] == candidate["id"]:
        continue

      if (member["id"], candidate["id"]) in past_pairs or (candidate["id"], member["id"]) in past_pairs:
        compatible = False
        break

      if score(member, candidate) < MIN_GROUP_SIMILARITY:
        compatible = False
        break

    if compatible:
      group.append(candidate)

  if len(group) < MIN_GROUP_SIZE:
    return None

  return group[1:]


@router.get("/history")
def get_match_history(user: CurrentUser, conn: psycopg.Connection = Depends(get_db)):
  """Returns match history for the current authenticated user."""

  rows = conn.execute(
    """
      SELECT
          m.id AS match_id,
          m.match_type,
          m.matched_at,
          m.conversation_topics,
          u.id AS participant_id,
          u.email,
          u.first_name,
          u.last_name,
          u.avatar_url,
          u.role_title,
          u.department
      FROM matches m
      JOIN match_participants mp
          ON mp.match_id = m.id
      JOIN users u
          ON u.id = mp.user_id
      WHERE m.id IN (
          SELECT match_id
          FROM match_participants
          WHERE user_id = %s
      )
      ORDER BY m.matched_at DESC
      """,
    (user["id"],),
  ).fetchall()

  matches = {}

  for row in rows:
    match_id = row["match_id"]

    if match_id not in matches:
      matches[match_id] = {
        "id": match_id,
        "match_type": row["match_type"],
        "matched_at": row["matched_at"],
        "conversation_topics": row["conversation_topics"] or [],
        "participants": [],
        "participant_ids": [user["id"]],  # include current user
      }

    if row["participant_id"] != user["id"]:
      matches[match_id]["participant_ids"].append(row["participant_id"])

      matches[match_id]["participants"].append(
        {
          "id": row["participant_id"],
          "email": row["email"],
          "first_name": row["first_name"],
          "last_name": row["last_name"],
          "avatar_url": row["avatar_url"],
          "role_title": row["role_title"],
          "department": row["department"],
        }
      )

  for match in matches.values():
    match["recommended_time"] = get_recommended_time_for_group(
      match["participant_ids"],
      conn,
    )

    del match["participant_ids"]

  return list(matches.values())


@router.post("/create")
def create_match(
  user: CurrentUser,
  conn: psycopg.Connection = Depends(get_db),
  body: MatchCreateRequest = Body(default_factory=MatchCreateRequest),
):
  try:
    # ---------------------------------------------------
    # Load current user
    # ---------------------------------------------------
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

    # ---------------------------------------------------
    # Available users (must have Slack linked so they can be notified)
    # ---------------------------------------------------
    all_users = conn.execute(
      """
            SELECT *
            FROM users
            WHERE is_available = TRUE
              AND slack_user_id IS NOT NULL
            """
    ).fetchall()

    # ===================================================
    # ONE-TO-ONE MATCH
    # ===================================================
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

      participant_ids = [
        db_user["id"],
        matched_user["id"],
      ]

      recommended_time = get_recommended_time_between_users(
        db_user["id"],
        matched_user["id"],
        conn,
      )

      conversation_topics = generate_conversation_topics(
        db_user,
        matched_user,
      )

      match_id = save_match(
        conn,
        participant_ids,
        "one_to_one",
        conversation_topics,
      )

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
        "participant_ids": participant_ids,
        "recommended_time": recommended_time,
        "conversation_topics": conversation_topics,
        "participants": [
          {
            "id": matched_user["id"],
            "first_name": matched_user["first_name"],
            "last_name": matched_user["last_name"],
            "email": matched_user["email"],
            "avatar_url": matched_user["avatar_url"],
            "role_title": matched_user["role_title"],
            "department": matched_user["department"],
          }
        ],
      }

    # ===================================================
    # GROUP MATCH
    # ===================================================
    group_members = find_group_match(
      conn,
      db_user,
      all_users,
    )

    if group_members is None:
      raise HTTPException(
        status_code=409,
        detail="Not enough compatible people for a group.",
      )

    all_participants = [db_user] + group_members

    participant_ids = [participant["id"] for participant in all_participants]

    recommended_time = get_recommended_time_for_group(
      participant_ids,
      conn,
    )

    conversation_topics = generate_group_conversation_topics(all_participants)

    match_id = save_match(
      conn,
      participant_ids,
      "group",
      conversation_topics,
    )

    for member in all_participants:
      other_members = [participant for participant in all_participants if participant["id"] != member["id"]]

      send_slack_match_notification(
        member["slack_user_id"],
        other_members,
        recommended_time,
        conversation_topics,
        is_group=True,
      )

    return {
      "id": match_id,
      "match_type": "group",
      "participant_ids": participant_ids,
      "recommended_time": recommended_time,
      "conversation_topics": conversation_topics,
      "participants": [
        {
          "id": participant["id"],
          "first_name": participant["first_name"],
          "last_name": participant["last_name"],
          "email": participant["email"],
          "avatar_url": participant["avatar_url"],
          "role_title": participant["role_title"],
          "department": participant["department"],
        }
        for participant in group_members
      ],
    }

  except HTTPException:
    raise

  except Exception as e:
    traceback.print_exc()
    raise HTTPException(
      status_code=500,
      detail=str(e),
    )
