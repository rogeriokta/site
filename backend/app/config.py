from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Correção de Cartões - API"
    debug: bool = True

    database_url: str = "sqlite+aiosqlite:///./data/correcao.db"

    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    upload_dir: str = "uploads"
    processed_dir: str = "processed"
    max_file_size_mb: int = 20

    allowed_origins: list[str] = ["*"]

    sentry_dsn: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
