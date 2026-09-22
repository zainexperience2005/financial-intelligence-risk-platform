"""Data models for context categories, items, and input budgets."""

from enum import StrEnum

from pydantic import BaseModel, Field


class ContextCategory(StrEnum):
    """Semantic category of a context item for priority-based selection."""

    SYSTEM = "system"
    CURRENT_REQUEST = "current_request"
    CONVERSATION = "conversation"
    TOOL_RESULT = "tool_result"
    RETRIEVAL = "retrieval"
    MEMORY = "memory"
    OTHER = "other"


class ContextItem(BaseModel):
    """An individual piece of typed context candidate for LLM prompt assembly."""

    content: str
    category: ContextCategory
    priority: int = Field(
        default=50,
        ge=0,
        le=100,
        description="Priority weight from 0 (lowest) to 100 (highest).",
    )
    required: bool = Field(
        default=False,
        description="If True, this item must not be silently discarded.",
    )
    source_id: str | None = Field(
        default=None,
        description="Unique identifier for correlation (e.g. message_id or chunk_id).",
    )
    estimated_tokens: int = Field(
        default=0,
        description="Estimated token length of the content.",
    )


class ContextBudget(BaseModel):
    """Defines maximum context window capacity and generation headroom."""

    max_tokens: int = Field(
        default=8_000,
        ge=1,
        description="Total context window ceiling.",
    )
    reserve_output_tokens: int = Field(
        default=1_000,
        ge=0,
        description="Tokens reserved strictly for model output generation.",
    )


class ContextBuildResult(BaseModel):
    """Result of deterministic context selection and budget evaluation."""

    selected: list[ContextItem]
    dropped: list[ContextItem]
    estimated_input_tokens: int
    available_input_tokens: int
