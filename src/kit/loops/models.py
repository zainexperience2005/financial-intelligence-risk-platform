"""Data models for loop control, budgets, and runtime status."""

from enum import StrEnum

from pydantic import BaseModel, Field


class StopReason(StrEnum):
    """Explicit, machine-readable reason why an agent loop halted."""

    COMPLETED = "completed"
    MAX_ITERATIONS = "max_iterations"
    MAX_TOOL_CALLS = "max_tool_calls"
    REPEATED_ACTION = "repeated_action"
    TOO_MANY_FAILURES = "too_many_failures"
    COST_BUDGET = "cost_budget"
    TOKEN_BUDGET = "token_budget"
    UNKNOWN_COST = "unknown_cost"
    CONTEXT_BUDGET = "context_budget"


class LoopBudget(BaseModel):
    """Configurable execution budget limits for an agent loop."""

    max_iterations: int = Field(
        default=8,
        ge=1,
        description="Maximum LLM reasoning cycles allowed before termination.",
    )

    max_tool_calls: int = Field(
        default=12,
        ge=1,
        description="Maximum total tool calls allowed across all iterations.",
    )

    max_failures: int = Field(
        default=3,
        ge=0,
        description="Maximum failed tool operations allowed before halting.",
    )

    max_repeated_actions: int = Field(
        default=2,
        ge=1,
        description="Maximum identical tool executions permitted.",
    )

    max_tokens: int | None = Field(
        default=None,
        ge=1,
        description="Cumulative token budget ceiling across the agent run.",
    )

    max_cost_usd: float | None = Field(
        default=None,
        ge=0,
        description="Cumulative estimated USD cost ceiling across the agent run.",
    )


class LoopUsage(BaseModel):
    """Current cumulative consumption metrics for the active loop."""

    iterations: int = 0
    tool_calls: int = 0
    failures: int = 0

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    estimated_cost_usd: float = 0.0
    cost_complete: bool = True


class LoopStatus(BaseModel):
    """Serializable runtime status of the loop controller, safe for checkpointing."""

    usage: LoopUsage = Field(default_factory=LoopUsage)
    stop_reason: StopReason | None = None
    stopped: bool = False
    action_counts: dict[str, int] = Field(default_factory=dict)
