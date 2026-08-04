import psycopg


def get_past_matches(conn: psycopg.Connection) -> set[tuple[int, int]]:
  """
  Claims all previous pairs from matches table into memory Set".
  """
  with conn.cursor() as cur:
    cur.execute("SELECT user1_id, user2_id FROM matches;")
    rows = cur.fetchall()

  past_pairs = set()
  for row in rows:
    # dict_row -- access with dict keys
    u1, u2 = row["user1_id"], row["user2_id"]
    past_pairs.add((u1, u2))
    past_pairs.add((u2, u1))
  return past_pairs


def save_matches(conn: psycopg.Connection, matches: list[tuple[int, int]]):
  """Saves new pairs into database."""
  with conn.cursor() as cur:
    for u1, u2 in matches:
      cur.execute("INSERT INTO matches (user1_id, user2_id) VALUES (%s, %s);", (u1, u2))
  conn.commit()
