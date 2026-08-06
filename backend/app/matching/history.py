import psycopg


def get_past_matches(conn: psycopg.Connection) -> set[tuple[int, int]]:
  """Завантажує всі попередні пари (із match_participants) у пам'ять."""
  with conn.cursor() as cur:
    cur.execute("""
            SELECT mp1.user_id AS user1_id, mp2.user_id AS user2_id
            FROM match_participants mp1
            JOIN match_participants mp2
              ON mp1.match_id = mp2.match_id AND mp1.user_id != mp2.user_id
        """)
    rows = cur.fetchall()

  past_pairs = set()
  for row in rows:
    u1, u2 = row["user1_id"], row["user2_id"]
    past_pairs.add((u1, u2))
    past_pairs.add((u2, u1))
  return past_pairs


def save_match(conn, participant_ids, match_type, conversation_topics):
  match = conn.execute(
    """
        INSERT INTO matches (match_type, conversation_topics)
        VALUES (%s, %s)
        RETURNING id
        """,
    (match_type, conversation_topics),
  ).fetchone()

  match_id = match["id"]

  for participant_id in participant_ids:
    conn.execute(
      """
            INSERT INTO match_participants (match_id, user_id)
            VALUES (%s, %s)
            """,
      (match_id, participant_id),
    )

  conn.commit()

  return match_id
