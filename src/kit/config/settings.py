from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Financial Intelligence & Risk Platform"
    app_version: str = "0.1.0"
    app_env: Literal[
        "development",
        "test",
        "production",
    ] = "development"
    environment: str = "development"
    debug: bool = False

    # LLM
    llm_provider: str = "openai"
    llm_model: str = "gpt-4.1-mini"
    openai_model: str = "gpt-4.1-mini"
    llm_temperature: float = 0.0
    llm_max_tokens: int | None = None

    # Database
    database_url: str = (
        "postgresql+psycopg://financial_app:"
        "financial_password@localhost:5432/"
        "financial_platform"
    )
    readonly_database_url: str = (
        "postgresql+psycopg://financial_reader:"
        "reader_dev_password@localhost:5432/"
        "financial_platform"
    )
    read_only_database_url: str = (
        "postgresql+psycopg://financial_reader:"
        "reader_dev_password@localhost:5432/"
        "financial_platform"
    )
    checkpoint_database_url: str = (
        "postgresql://financial_app:"
        "financial_password@localhost:5432/"
        "financial_platform"
    )

    # Postgres config for compose
    postgres_db: str = "financial_platform"
    postgres_user: str = "financial_app"
    postgres_password: str = "financial_password"

    # OPENAI
    openai_api_key: str | None = None
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "financial_policies"
    memory_qdrant_collection: str = "financial_memory"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Logging
    log_level: str = "INFO"

    @model_validator(mode="after")
    def sync_readonly_urls(self) -> "Settings":
        if self.readonly_database_url != self.read_only_database_url:
            # Prefer the explicitly set one
            if (
                self.readonly_database_url
                != "postgresql+psycopg://financial_reader:reader_dev_password@localhost:5432/financial_platform"
            ):
                self.read_only_database_url = self.readonly_database_url
            else:
                self.readonly_database_url = self.read_only_database_url
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
