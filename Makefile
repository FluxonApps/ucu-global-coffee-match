.PHONY: db db-stop db-clear backend frontend

db:
	docker compose up -d --wait db
	cd backend && uv run python -m app.scripts.init_db

db-stop:
	docker compose stop db

db-clear:
	cd backend && uv run python -m app.scripts.reset_db

backend:
	cd backend && uv run uvicorn app.main:app --reload

frontend:
	cd frontend && npm run dev
