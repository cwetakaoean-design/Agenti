"""Application settings loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime config. Reads from env vars and .env (development only)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")

    # Storage
    database_url: str = Field(default="sqlite:///./agenti.db")

    # GigaChat (Сбер)
    gigachat_auth_key: str = Field(default="", description="Base64 of client_id:secret")
    gigachat_scope: str = Field(default="GIGACHAT_API_PERS")
    gigachat_model: str = Field(default="GigaChat")

    # When true (or when no GigaChat key is set) agents use a deterministic
    # offline stub instead of calling the real LLM. Keeps tests/CI hermetic.
    use_stub_llm: bool = Field(default=False)

    def llm_is_stub(self) -> bool:
        return self.use_stub_llm or not self.gigachat_auth_key


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
