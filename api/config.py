"""Centralized settings loaded from env."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://ranger:ranger@postgres:5432/ranger"
    ranger_encryption_key: str = ""
    admin_token: str = "change-me-dev-only"

    mock_device_api_url: str = "http://mock-device-api:8001"
    chroma_persist_dir: str = "/data/chroma"
    runbooks_dir: str = "/data/runbooks"

    cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chroma_collection: str = "runbooks"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    s = Settings()
    if not s.ranger_encryption_key:
        raise RuntimeError(
            "RANGER_ENCRYPTION_KEY is not set. Generate one with:\n"
            '  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"\n'
            "and add it to your .env file."
        )
    return s
