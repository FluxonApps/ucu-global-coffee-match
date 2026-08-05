from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
  model_config = SettingsConfigDict(env_file=".env", extra="ignore")

  cors_origins: list[str] = [
    "http://localhost:5173",
    "http://localhost:5174",
  ]
  database_url: str = "postgresql://postgres:postgres@localhost:5432/coffee_match"
  cookie_secure: bool = False

  @field_validator("database_url", mode="before")
  @classmethod
  def assemble_db_connection(cls, v: str) -> str:
    if isinstance(v, str):
      if v.startswith("postgres://"):
        v = v.replace("postgres://", "postgresql://", 1)
    return v


settings = Settings()
