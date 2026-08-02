# Backend

FastAPI backend with cookie-session authentication, managed with [uv](https://docs.astral.sh/uv/).

## Setup

1. Install dependencies:

   ```shell
   uv sync
   ```

2. Copy `.env.example` to `.env` and adjust as needed:

   ```shell
   cp .env.example .env
   ```

3. Start Postgres and set up the schema (see the root `Makefile` — `make db` does this for you).

4. Run the dev server:

   ```shell
   uv run uvicorn app.main:app --reload
   ```

5. API docs live at http://localhost:8000/docs

## Auth

Session-based auth, no JWTs:

- `POST /auth/register` — hashes the password with bcrypt, creates a `users` row, opens a session.
- `POST /auth/login` — verifies the password, opens a session.
- `POST /auth/logout` — deletes the session row.
- `GET /auth/me` — resolves the current user from the session cookie.
- `GET /users/me` / `PATCH /users/me` — read/update the profile (name, team, timezone).

A session is a random token (`secrets.token_urlsafe(32)`) stored in the `sessions` table and set
as an `httponly` cookie. There's no separate refresh flow — logging out just deletes the row.

## Database

- `db/schema.sql` — source of truth for the schema (`CREATE TABLE IF NOT EXISTS`, safe to re-run).
- `db/seed.sql` — demo users (`alice@example.com` / `bob@example.com`, password `password123`).
- `app/scripts/init_db.py` — applies the schema and seeds only if `users` is empty. Used by
  `make db`.
- `app/scripts/reset_db.py` — drops and recreates everything, always reseeds. Used by
  `make clear-db`.

## Linting

```shell
uv run ruff check .
uv run ruff format .
```
