from collections.abc import Iterator

import psycopg
from psycopg.rows import dict_row

from app.settings import settings


def get_connection() -> psycopg.Connection:
  return psycopg.connect(settings.database_url, row_factory=dict_row)


def get_db() -> Iterator[psycopg.Connection]:
  conn = get_connection()
  try:
    yield conn
    conn.commit()  # Фіксуємо зміни в БД після успішного оброблення запиту
  except Exception:
    conn.rollback()  # Відкочуємо транзакцію у разі помилки
    raise
  finally:
    conn.close()
