"""Deterministic context builder with priority degradation and required guards."""

from collections.abc import Callable

from kit.context.estimator import (
    estimate_tokens,
)
from kit.context.models import (
    ContextBudget,
    ContextBuildResult,
    ContextItem,
)


class ContextBudgetExceededError(ValueError):
    """Raised when required context exceeds the available input budget."""


class ContextBuilder:
    """Assembles prompt context under a strict deterministic token budget.

    Guarantees:
    - Never silently drops required context (raises ContextBudgetExceededError).
    - Sorts optional items by priority descending and fills until headroom is exhausted.
    - Preserves output generation reservation (max_tokens - reserve_output_tokens).
    """

    def __init__(
        self,
        *,
        budget: ContextBudget,
        token_counter: Callable[[str], int] | None = None,
    ):
        self.budget = budget
        self.token_counter = token_counter

    def build(
        self,
        items: list[ContextItem],
    ) -> ContextBuildResult:
        """Evaluate candidate items and produce bounded selected and dropped subsets."""
        available = self.budget.max_tokens - self.budget.reserve_output_tokens

        if available <= 0:
            raise ContextBudgetExceededError("No input context budget available.")

        prepared: list[ContextItem] = []

        for item in items:
            prepared.append(
                item.model_copy(
                    update={
                        "estimated_tokens": estimate_tokens(
                            item.content,
                            self.token_counter,
                        )
                    }
                )
            )

        required = [item for item in prepared if item.required]
        optional = [item for item in prepared if not item.required]

        required_tokens = sum(item.estimated_tokens for item in required)

        if required_tokens > available:
            raise ContextBudgetExceededError(
                "Required context exceeds the available context budget."
            )

        # Sort optional items by priority descending
        optional.sort(
            key=lambda item: item.priority,
            reverse=True,
        )

        selected = list(required)
        dropped: list[ContextItem] = []

        used = required_tokens

        for item in optional:
            if used + item.estimated_tokens <= available:
                selected.append(item)
                used += item.estimated_tokens
            else:
                dropped.append(item)

        return ContextBuildResult(
            selected=selected,
            dropped=dropped,
            estimated_input_tokens=used,
            available_input_tokens=available,
        )
