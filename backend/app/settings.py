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
