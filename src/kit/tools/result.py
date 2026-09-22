"""Standardized result and error envelopes for tool execution."""

from typing import Any

from pydantic import BaseModel, field_validator


class ToolError(BaseModel):
    """Structured machine-readable error details for a failed tool operation."""

    code: str
    message: str
    retryable: bool = False

    def __eq__(self, other: Any) -> bool:
        """Allow backward-compatible equality comparison against plain strings."""
        if isinstance(other, str):
            return self.message == other
        return super().__eq__(other)

    def __str__(self) -> str:
        return self.message


class ToolResult(BaseModel):
    """Canonical envelope returned by tools across the agent platform."""

    success: bool
    data: Any | None = None
    error: ToolError | None = None

    @field_validator("error", mode="before")
    @classmethod
    def _validate_error(cls, v: Any) -> Any:
        """Coerce plain error strings into structured ToolError instances."""
        if isinstance(v, str):
            return ToolError(code="ERROR", message=v, retryable=False)
        return v

    @classmethod
    def ok(
        cls,
        data: Any = None,
    ) -> "ToolResult":
        """Construct a successful ToolResult envelope."""
        return cls(
            success=True,
            data=data,
        )

    @classmethod
    def fail(
        cls,
        *,
        code: str,
        message: str,
        retryable: bool = False,
    ) -> "ToolResult":
        """Construct a failed ToolResult envelope with typed error metadata."""
        return cls(
            success=False,
            error=ToolError(
                code=code,
                message=message,
                retryable=retryable,
            ),
        )
