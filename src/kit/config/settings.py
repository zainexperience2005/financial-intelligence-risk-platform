from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Financial Intelligence & Risk Platform"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False

    # LLM
    llm_provider: str = "openai"
    llm_model: str = "gpt-4.1-mini"
    llm_temperature: float = 0.0
    llm_max_tokens: int | None = None

    database_url: str = (
    "postgresql+psycopg://financial_user:"
    "financial_password@localhost:5432/"
    "financial_platform"
)

    # OPENAI
    openai_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()