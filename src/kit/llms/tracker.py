"""Tracks token usage and calculates estimated invocation costs.

Uses a PricingRegistry to look up per-model pricing rates.
"""

from langchain_core.messages import AIMessage

from kit.llms.pricing import calculate_cost
from kit.llms.pricing_registry import PricingRegistry
from kit.llms.usage import ModelUsage
from kit.llms.usage_extractor import extract_token_usage


class UsageTracker:
    """Tracks token consumption and computes estimated cost for each LLM invocation."""

    def __init__(
        self,
        pricing_registry: PricingRegistry | None = None,
    ):
        self.pricing_registry = pricing_registry or PricingRegistry()

    def track(
        self,
        *,
        model: str,
        message: AIMessage,
    ) -> ModelUsage:
        """Extract tokens from metadata and calculate cost with registered pricing.

        If the model is not in the pricing registry, estimated_cost_usd is None.
        """
        tokens = extract_token_usage(message)

        pricing = self.pricing_registry.get(model)

        cost: float | None = None

        if pricing is not None:
            cost = calculate_cost(
                input_tokens=tokens.input_tokens,
                output_tokens=tokens.output_tokens,
                cached_input_tokens=tokens.cached_input_tokens,
                pricing=pricing,
            )

        return ModelUsage(
            model=model,
            tokens=tokens,
            estimated_cost_usd=cost,
        )
