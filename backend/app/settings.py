import json

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
  model_config = SettingsConfigDict(env_file=".env", extra="ignore")

  cors_origins: list[str] = [
    "http://localhost:5173",
    "http://localhost:5174",
    "https://coffee-match.pp.ua",
    "https://www.coffee-match.pp.ua",
    "https://coffee-match-frontend.onrender.com",
  ]
  database_url: str = "postgresql://postgres:postgres@localhost:5432/coffee_match"
  cookie_secure: bool = False
  gemini_project_id: str = ""
  gemini_location: str = "us-central1"
  google_application_credentials: str = ""
  google_client_id: str = ""
  google_client_secret: str = ""
  google_redirect_uri: str = "http://localhost:8000/users/me/calendar/callback"
  frontend_url: str = "http://localhost:5173"
  google_token_encryption_key: str = ""

  @field_validator("cors_origins", mode="before")
  @classmethod
  def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
    if isinstance(v, str):
      v = v.strip()
      # Підтримка JSON-формату: '["https://...", "http://..."]'
      if v.startswith("[") and v.endswith("]"):
        return json.loads(v)
      # Підтримка формату через кому: "https://...,http://..."
      return [item.strip() for item in v.split(",") if item.strip()]
    return v

  @field_validator("database_url", mode="before")
  @classmethod
  def assemble_db_connection(cls, v: str) -> str:
    if isinstance(v, str):
      v = v.strip()
      if v.startswith("postgres://"):
        v = v.replace("postgres://", "postgresql://", 1)
    return v


settings = Settings()
