import pathlib

from app.db import get_connection

DB_DIR = pathlib.Path(__file__).parents[2] / "db"


def main() -> None:
    conn = get_connection()
    try:
        conn.execute("DROP TABLE IF EXISTS sessions, users CASCADE")
        conn.execute(DB_DIR.joinpath("schema.sql").read_text())
        conn.execute(DB_DIR.joinpath("seed.sql").read_text())
        conn.commit()
        print("Database reset and seeded.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
