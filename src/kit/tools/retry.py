"""Retry configuration policies for tool execution."""

from pydantic import BaseModel, Field


class RetryPolicy(BaseModel):
    """Configures bounded retry behavior with backoff for transient errors."""

    max_attempts: int = Field(
        default=3,
        ge=1,
        description="Total execution attempts (initial attempt + retries).",
    )

    initial_delay_seconds: float = Field(
        default=0.25,
        ge=0,
        description="Delay in seconds before the first retry attempt.",
    )

    backoff_multiplier: float = Field(
        default=2.0,
        ge=1,
        description="Multiplicative factor applied to delay on subsequent retries.",
    )

    max_delay_seconds: float = Field(
        default=2.0,
        ge=0,
        description="Maximum delay ceiling between retry attempts.",
    )
