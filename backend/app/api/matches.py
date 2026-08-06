from fastapi import APIRouter, Depends

from app.db import get_connection
from app.dependencies import get_current_user  # <-- Вкажіть правильний шлях до вашої функції

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("/history")
def get_match_history(user: dict = Depends(get_current_user)):
  conn = get_connection()
  try:
    rows = conn.execute(
      """
            SELECT
                m.id,
                m.match_type,
                m.status,
                m.conversation_topics,
                m.matched_at,
                m.notified_at,
                COALESCE(
                    json_agg(
                        json_build_object(
                            'id', u.id,
                            'first_name', u.first_name,
                            'last_name', u.last_name,
                            'avatar_url', u.avatar_url,
                            'role_title', u.role_title,
                            'department', u.department
                        )
                    ) FILTER (WHERE u.id IS NOT NULL AND u.id != %s),
                    '[]'
                ) AS partners
            FROM matches m
            JOIN match_participants mp ON m.id = mp.match_id
            LEFT JOIN match_participants mp_partner ON m.id = mp_partner.match_id AND mp_partner.user_id != %s
            LEFT JOIN users u ON mp_partner.user_id = u.id
            WHERE mp.user_id = %s
            GROUP BY m.id
            ORDER BY m.matched_at DESC;
        """,
      (user["id"], user["id"], user["id"]),
    ).fetchall()

    return rows
  finally:
    conn.close()
