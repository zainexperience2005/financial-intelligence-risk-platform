"""Restorable LoopController for deterministic execution bounds and budgeting."""

from kit.loops.models import (
    LoopBudget,
    LoopStatus,
    StopReason,
)
from kit.loops.signatures import (
    create_action_signature,
)


class LoopController:
    """Controls agent loop termination and enforces multi-dimensional budgets.

    This controller is restorable from serializable state (LoopBudget and LoopStatus),
    avoiding storing active runtime objects in LangGraph checkpoint state.
    """

    def __init__(
        self,
        budget: LoopBudget | None = None,
        status: LoopStatus | None = None,
    ):
        self.budget = budget or LoopBudget()
        self.status = status or LoopStatus()

    def start_iteration(self) -> None:
        """Record the start of a reasoning iteration and enforce iteration budget."""
        if self.status.stopped:
            return

        self.status.usage.iterations += 1

        if self.status.usage.iterations > self.budget.max_iterations:
            self.stop(StopReason.MAX_ITERATIONS)

    def record_tool_call(
        self,
        name: str,
        arguments: dict,
    ) -> None:
        """Record a proposed tool call and detect repetition before execution."""
        if self.status.stopped:
            return

        self.status.usage.tool_calls += 1

        if self.status.usage.tool_calls > self.budget.max_tool_calls:
            self.stop(StopReason.MAX_TOOL_CALLS)
            return

        signature = create_action_signature(
            name,
            arguments,
        )

        count = self.status.action_counts.get(signature, 0) + 1
        self.status.action_counts[signature] = count

        if count > self.budget.max_repeated_actions:
            self.stop(StopReason.REPEATED_ACTION)

    def record_failure(self) -> None:
        """Record a permanently failed tool operation and enforce failure budget."""
        if self.status.stopped:
            return

        self.status.usage.failures += 1

        if self.status.usage.failures > self.budget.max_failures:
            self.stop(StopReason.TOO_MANY_FAILURES)

    def record_usage(
        self,
        *,
        input_tokens: int = 0,
        output_tokens: int = 0,
        tokens: int = 0,
        cost_usd: float | None = None,
    ) -> None:
        """Record token consumption and estimated cost, enforcing spend ceilings.

        Implements fail-closed behavior: if a cost budget is configured but the call
        could not be priced (cost_usd is None), the loop stops with UNKNOWN_COST.
        """
        if self.status.stopped:
            return

        if tokens > 0 and input_tokens == 0 and output_tokens == 0:
            input_tokens = tokens

        total = input_tokens + output_tokens

        self.status.usage.input_tokens += input_tokens
        self.status.usage.output_tokens += output_tokens
        self.status.usage.total_tokens += total

        if cost_usd is None:
            self.status.usage.cost_complete = False
        else:
            self.status.usage.estimated_cost_usd += cost_usd

        # Token budget check
        if (
            self.budget.max_tokens is not None
            and self.status.usage.total_tokens > self.budget.max_tokens
        ):
            self.stop(StopReason.TOKEN_BUDGET)
            return

        # Fail closed on unpriced call when cost budget is required
        if self.budget.max_cost_usd is not None and cost_usd is None:
            self.stop(StopReason.UNKNOWN_COST)
            return

        # Cost budget check
        if (
            self.budget.max_cost_usd is not None
            and self.status.usage.estimated_cost_usd > self.budget.max_cost_usd
        ):
            self.stop(StopReason.COST_BUDGET)

    def complete(self) -> None:
        """Explicitly mark normal successful completion."""
        self.stop(StopReason.COMPLETED)

    def stop(
        self,
        reason: StopReason,
    ) -> None:
        """Halt loop execution with an explicit stop reason."""
        self.status.stopped = True
        self.status.stop_reason = reason

    @property
    def can_continue(self) -> bool:
        """Return True if loop has not been halted by any stop condition."""
        return not self.status.stopped
