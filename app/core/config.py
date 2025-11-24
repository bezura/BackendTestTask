import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class EnvBaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class ProjectSettings(EnvBaseSettings):
    TITLE: str = "Reviewer Service"
    DESCRIPTION: str = "Reviewer Service"
    VERSION: str = "1.0.0"
    API_V1_PATH: str = "/api/v1"
    DEBUG: bool = False
    CORS_ORIGINS: list[str] = ["localhost", "*"]


class DBSettings(EnvBaseSettings):
    DB_HOST: str = "postgres"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASS: str | None = None
    DB_NAME: str = "postgres"

    @property
    def database_url_psycopg2(self) -> str:
        if self.DB_PASS:
            return (
                f"postgresql://{self.DB_USER}:{self.DB_PASS}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )
        return f"postgresql://{self.DB_USER}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def postgres_async_url(self) -> str:
        # SQLAlchemy async driver
        if self.DB_PASS:
            return (
                f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )
        return f"postgresql+asyncpg://{self.DB_USER}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


class Settings(ProjectSettings, DBSettings):
    pass


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


logging_conf = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "{name} {levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
    },
    "loggers": {
        "": {
            "level": os.getenv("LOG_LEVEL", "DEBUG"),
            "handlers": ["console"],
            "propagate": True,
        }
    },
}
