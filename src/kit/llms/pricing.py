"""Model pricing configuration and deterministic cost calculation."""

from pydantic import BaseModel


class ModelPricing(BaseModel):
    """Pricing rates per 1,000,000 tokens for a specific model."""

    input_per_million: float
    output_per_million: float
    cached_input_per_million: float | None = None


def calculate_cost(
    *,
    input_tokens: int,
    output_tokens: int,
    cached_input_tokens: int = 0,
    pricing: ModelPricing,
) -> float:
    """Calculate estimated USD cost for given token usage and pricing structure."""
    uncached_input = max(
        input_tokens - cached_input_tokens,
        0,
    )

    input_cost = uncached_input / 1_000_000 * pricing.input_per_million

    output_cost = output_tokens / 1_000_000 * pricing.output_per_million

    cached_cost = 0.0

    if cached_input_tokens > 0 and pricing.cached_input_per_million is not None:
        cached_cost = cached_input_tokens / 1_000_000 * pricing.cached_input_per_million

    return input_cost + output_cost + cached_cost
