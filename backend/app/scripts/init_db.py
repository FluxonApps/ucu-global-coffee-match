import pathlib

from app.db import get_connection

DB_DIR = pathlib.Path(__file__).parents[2] / "db"


def main() -> None:
  conn = get_connection()
  try:
    # Створюємо таблиці за новим schema.sql
    conn.execute(DB_DIR.joinpath("schema.sql").read_text(encoding="utf-8"))
    conn.commit()

    # Заповнюємо тестовими даними
    conn.execute(DB_DIR.joinpath("seed.sql").read_text(encoding="utf-8"))
    conn.commit()
    print("Database re-created and seeded successfully.")
  finally:
    conn.close()


if __name__ == "__main__":
  main()
