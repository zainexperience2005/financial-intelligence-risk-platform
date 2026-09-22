"""Data models for token usage and estimated model costs."""

from pydantic import BaseModel


class TokenUsage(BaseModel):
    """Normalized token consumption metrics."""

    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        """Total input and output tokens consumed."""
        return self.input_tokens + self.output_tokens


class ModelUsage(BaseModel):
    """Model invocation usage metrics including tokens and estimated cost in USD."""

    model: str
    tokens: TokenUsage
    estimated_cost_usd: float | None = None
