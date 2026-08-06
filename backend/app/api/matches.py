import os
import traceback
from typing import Literal

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from slack_sdk import WebClient

from app.api.availability import get_recommended_time_between_users
from app.auth import CurrentUser
from app.db import get_db
from app.matching.history import get_past_matches, save_match
from app.matching.similarity import score
from app.services.topics import generate_conversation_topics

router = APIRouter(prefix="/matches", tags=["matches"])

# Slack Client
slack_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN")) if os.environ.get("SLACK_BOT_TOKEN") else None


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
  """Надсилає детальне сповіщення про match у Slack бота."""
  if not slack_client or not recipient_slack_id:
    return

  header_text = "🎉 *Знайдено груповий Coffee Match!*" if is_group else "🎉 *Знайдено новий 1-on-1 Coffee Match!*"

  blocks = [
    {"type": "section", "text": {"type": "mrkdwn", "text": header_text}},
    {"type": "divider"},
  ]

  for partner in partners_info:
    name = f"{partner.get('first_name', '')} {partner.get('last_name', '')}".strip()
    role = partner.get("role_title") or "Не вказано"
    dept = partner.get("department") or "Не вказано"
    bio = partner.get("bio") or "Не вказано"

    interests = partner.get("personal_interests") or []
    interests_str = ", ".join(interests) if interests else "Не вказано"

    skills = partner.get("skills") or []
    skills_str = ", ".join(skills) if skills else "Не вказано"

    user_text = (
      f"👤 *Співрозмовник:* <@{partner['slack_user_id']}> ({name})\n"
      f"💼 *Посада:* {role} | *Відділ:* {dept}\n"
      f"📝 *Про себе:* {bio}\n"
      f"🎯 *Інтереси:* {interests_str}\n"
      f"💡 *Навички:* {skills_str}"
    )

    blocks.append(
      {
        "type": "section",
        "text": {"type": "mrkdwn", "text": user_text},
      }
    )
    blocks.append({"type": "divider"})

  # Рекомендований час
  if recommended_time:
    blocks.append(
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": f"⏰ *Рекомендований час для зустрічі:*\n{recommended_time}",
        },
      }
    )

  # Теми для розмови / Icebreakers
  if topics:
    topics_formatted = "\n".join([f"• {t}" for t in topics])
    blocks.append(
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": f"💬 *Ідеї для початку розмови:*\n{topics_formatted}",
        },
      }
    )

  try:
    slack_client.chat_postMessage(channel=recipient_slack_id, blocks=blocks)
  except Exception as e:
    print(f"Error sending Slack notification to {recipient_slack_id}: {e}")


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
  past_pairs = get_past_matches(conn)
  candidates = []

  for candidate in all_users:
    if candidate["id"] == user["id"]:
      continue
    # Рахуємо бал схожості з ініціатором
    candidate_score = score(user, candidate)
    candidates.append((candidate_score, candidate))

  # Сортуємо кандидатів за найкращим балом
  candidates.sort(key=lambda x: x[0], reverse=True)

  needed_count = group_size - 1
  if len(candidates) < needed_count:
    return None

  selected_group = [item[1] for item in candidates[:needed_count]]
  return selected_group


@router.get("/history")
def get_match_history(user: CurrentUser, conn: psycopg.Connection = Depends(get_db)):
  """Повертає історію матчів поточного користувача."""
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
  body: MatchCreateRequest = MatchCreateRequest(),
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

    # Отримуємо всіх доступних користувачів з прив'язаним Slack
    all_users = conn.execute("""
            SELECT *
            FROM users
            WHERE slack_user_id IS NOT NULL
              AND is_available = true
        """).fetchall()

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

      # 1. Розрахунок часу та генерація тем
      recommended_time = get_recommended_time_between_users(db_user["id"], matched_user["id"], conn)
      conversation_topics = generate_conversation_topics(db_user, matched_user)

      # 2. Збереження матчу в БД
      match_id = save_match(
        conn,
        [db_user["id"], matched_user["id"]],
        "one_to_one",
        conversation_topics,
      )

      # 3. Відправка повідомлень у Slack обом учасникам
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

    # Груповий match
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
        detail=(f"Not enough compatible people for a group of {body.group_size}"),
      )

    all_participants = [db_user] + group_members
    participant_ids = [m["id"] for m in all_participants]

    # Генерація тем для групи
    conversation_topics = generate_conversation_topics(db_user, group_members[0])

    match_id = save_match(
      conn,
      participant_ids,
      "group",
      conversation_topics,
    )

    # Розсилання повідомлень кожному учаснику групи
    for member in all_participants:
      other_partners = [p for p in all_participants if p["id"] != member["id"]]
      send_slack_match_notification(
        member["slack_user_id"],
        other_partners,
        None,  # Рекомендований час для групи (за потреби)
        conversation_topics,
        is_group=True,
      )

    return {
      "id": match_id,
      "match_type": "group",
      "participant_ids": participant_ids,
      "conversation_topics": conversation_topics,
    }

  except Exception:
    traceback.print_exc()
    raise