"""Decoupled pricing registry for registering and retrieving model pricing rates."""

from kit.llms.pricing import ModelPricing


class PricingRegistry:
    """Registry maintaining pricing configurations decoupled from loop mechanics."""

    def __init__(self) -> None:
        self._prices: dict[str, ModelPricing] = {}

    def register(
        self,
        model: str,
        pricing: ModelPricing,
    ) -> None:
        """Register pricing rates for a given model identifier."""
        self._prices[model] = pricing

    def get(
        self,
        model: str,
    ) -> ModelPricing | None:
        """Retrieve registered pricing for a model, or None if unpriced."""
        return self._prices.get(model)
