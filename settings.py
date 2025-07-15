from pathlib import Path

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8")

    pg_dsn: PostgresDsn = Field(alias="DATABASE_URL")
    enable_kube: bool
    kube_config_path: Path | None = None
    kube_context: str | None = None
    kube_namespace: str | None = None

settings = Settings() # type: ignore[call-arg]
