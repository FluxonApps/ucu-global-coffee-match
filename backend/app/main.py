from contextlib import asynccontextmanager

import psycopg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, match, users
from app.db import get_connection, init_db
from app.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1")
        init_db()
    except psycopg.OperationalError as exc:
        raise RuntimeError(
            f"Could not connect to the database at {settings.database_url!r}. Is Postgres running? Try `make db`."
        ) from exc

    yield


app = FastAPI(title="Global Coffee Match API", lifespan=lifespan)

app.add_middleware(
  CORSMiddleware,
  allow_origins=settings.cors_origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(match.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
