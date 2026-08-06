import pathlib

from app.db import get_connection

DB_DIR = pathlib.Path(__file__).parents[2] / "db"


def main() -> None:
  conn = get_connection()
  try:
    # 1. Запуск основної схеми
    conn.execute(DB_DIR.joinpath("schema.sql").read_text(encoding="utf-8"))

    # 2. Автоматична міграція для існуючих таблиць
    conn.execute("""
        ALTER TABLE matches
        ADD COLUMN IF NOT EXISTS conversation_topics JSONB;
    """)
    conn.commit()

    # 3. Перевірка даних та сидінг
    row = conn.execute("SELECT count(*) AS count FROM users").fetchone()
    if row["count"] == 0:
      conn.execute(DB_DIR.joinpath("seed.sql").read_text(encoding="utf-8"))
      conn.commit()
      print("Seeded database.")
    else:
      print("Database already has data, skipping seed.")
  finally:
    conn.close()


if __name__ == "__main__":
  main()
