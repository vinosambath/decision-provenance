from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://provenance:provenance@localhost:5432/provenance"
    trace_dir: Path = Path("traces")
    default_max_tokens: int = 200_000
    default_max_calls: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
