"""Application configuration."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .constants import SUPPORTED_INTERVALS, SUPPORTED_SYMBOLS


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    database_url: str = Field(default="sqlite:///./paper_trading.db", alias="DATABASE_URL")
    binance_base_url: str = Field(default="https://api.binance.com", alias="BINANCE_BASE_URL")
    request_timeout_seconds: float = Field(default=15.0, alias="REQUEST_TIMEOUT_SECONDS")
    ntfy_topic_url: str | None = Field(default=None, alias="NTFY_TOPIC_URL")
    ntfy_access_token: str | None = Field(default=None, alias="NTFY_ACCESS_TOKEN")
    default_candle_limit: int = Field(default=300, alias="DEFAULT_CANDLE_LIMIT")
    symbol_allowlist: list[str] = Field(default_factory=lambda: sorted(SUPPORTED_SYMBOLS), alias="SYMBOL_ALLOWLIST")
    interval_allowlist: list[str] = Field(
        default_factory=lambda: sorted(SUPPORTED_INTERVALS), alias="INTERVAL_ALLOWLIST"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("symbol_allowlist", mode="before")
    @classmethod
    def parse_symbol_allowlist(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip().upper() for item in value.split(",") if item.strip()]
        return [item.upper() for item in value]

    @field_validator("interval_allowlist", mode="before")
    @classmethod
    def parse_interval_allowlist(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
