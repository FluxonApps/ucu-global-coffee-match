import pathlib

from app.db import get_connection

DB_DIR = pathlib.Path(__file__).parents[2] / "db"


def main() -> None:
  conn = get_connection()
  try:
    conn.execute(DB_DIR.joinpath("schema.sql").read_text())
    conn.commit()

    row = conn.execute("SELECT count(*) AS count FROM users").fetchone()
    if row["count"] == 0:
      conn.execute(DB_DIR.joinpath("seed.sql").read_text())
      conn.commit()
      print("Seeded database.")
    else:
      print("Database already has data, skipping seed.")
  finally:
    conn.close()


if __name__ == "__main__":
  main()
