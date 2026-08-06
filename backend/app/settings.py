from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
  model_config = SettingsConfigDict(env_file=".env", extra="ignore")

  cors_origins: list[str] = ["http://localhost:5173", "http://localhost:5174"]
  database_url: str = "postgresql://postgres:postgres@localhost:5432/coffee_match"
  cookie_secure: bool = False
  gemini_project_id: str = ""
  gemini_location: str = "us-central1"
  google_application_credentials: str = ""


settings = Settings()