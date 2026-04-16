from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Payment Service"
    api_key: str = "super-secret-key"

    database_url: str = "postgresql+asyncpg://payment:payment@127.0.0.1:5432/payment_service"
    sync_database_url: str = "postgresql+psycopg://payment:payment@127.0.0.1:5432/payment_service"
    rabbitmq_url: str = "amqp://guest:guest@127.0.0.1:5672/"

    outbox_poll_interval_seconds: float = Field(default=1.0, ge=0.2, le=10.0)
    webhook_timeout_seconds: float = Field(default=5.0, ge=1.0, le=60.0)
    consumer_max_attempts: int = Field(default=3, ge=1, le=10)


@lru_cache
def get_settings() -> Settings:
    return Settings()
