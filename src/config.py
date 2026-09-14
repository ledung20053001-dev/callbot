from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and ``.env``."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "ai-clinic-callbot"
    app_env: str = "development"
    app_debug: bool = False
    enable_debug_interface: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
