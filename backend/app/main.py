from contextlib import asynccontextmanager

import psycopg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, availability, matches, users
from app.db import get_connection
from app.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
  try:
    with get_connection() as conn:
      conn.execute("SELECT 1")
  except psycopg.OperationalError as exc:
    raise RuntimeError(
      f"Could not connect to the database at {settings.database_url!r}. Is Postgres running? Try `make db`."
    ) from exc

  yield  # <-- Додано yield за межами try/except


app = FastAPI(title="Global Coffee Match API", lifespan=lifespan)

# Переконуємося, що cors_origins є списком (якщо зі змінних оточення передається рядок)
if isinstance(settings.cors_origins, str):
  cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
else:
  cors_origins = settings.cors_origins

app.add_middleware(
  CORSMiddleware,
  allow_origins=cors_origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(matches.router)
app.include_router(availability.router)
app.include_router(google_calendar.router)


# Обробник для кореневого шляху (приймає і GET, і HEAD)
@app.api_route("/", methods=["GET", "HEAD"])
async def root():
  return {"status": "ok", "message": "Global Coffee Match API"}


@app.get("/health")
async def health():
  return {"status": "ok"}
