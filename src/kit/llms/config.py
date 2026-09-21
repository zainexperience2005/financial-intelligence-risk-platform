from typing import Literal

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    provider: Literal["openai"] = "openai"

    model: str = "gpt-4.1-mini"

    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
    )

    max_tokens: int | None = Field(
        default=None,
        gt=0,
    )

    api_key: str | None = Field(
        default=None,
        description="API key for the LLM provider",
    )
