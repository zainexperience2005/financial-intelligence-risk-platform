"""Controlled tool executor with bounded retries and exception sanitization."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from kit.tools.exceptions import (
    PermanentToolError,
    RetryableToolError,
)
from kit.tools.result import ToolResult
from kit.tools.retry import RetryPolicy

ToolCallable = Callable[
    [dict[str, Any]],
    Awaitable[ToolResult],
]


class ToolExecution:
    """Encapsulates the final outcome and attempt count of a tool execution."""

    def __init__(
        self,
        *,
        result: ToolResult,
        attempts: int,
    ):
        self.result = result
        self.attempts = attempts


class ControlledToolExecutor:
    """Executes tools under strict retry policies and catches unexpected exceptions.

    Guarantees:
    - Retries retryable errors up to max_attempts with exponential backoff.
    - Halts immediately on permanent failures (validation, permissions, deterministic).
    - Sanitizes unexpected exceptions into INTERNAL_TOOL_ERROR without leaking secrets.
    """

    def __init__(
        self,
        retry_policy: RetryPolicy | None = None,
    ):
        self.retry_policy = retry_policy or RetryPolicy()

    async def execute(
        self,
        *,
        tool: ToolCallable,
        arguments: dict[str, Any],
    ) -> ToolExecution:
        """Execute a tool callable under the configured retry policy."""
        delay = self.retry_policy.initial_delay_seconds

        last_result: ToolResult | None = None

        for attempt in range(
            1,
            self.retry_policy.max_attempts + 1,
        ):
            try:
                result = await tool(arguments)
            except RetryableToolError as exc:
                result = ToolResult.fail(
                    code="RETRYABLE_TOOL_ERROR",
                    message=str(exc),
                    retryable=True,
                )
            except PermanentToolError as exc:
                result = ToolResult.fail(
                    code="PERMANENT_TOOL_ERROR",
                    message=str(exc),
                    retryable=False,
                )
            except Exception:
                # Sanitize unexpected exceptions to protect sensitive secrets
                result = ToolResult.fail(
                    code="INTERNAL_TOOL_ERROR",
                    message="Tool execution failed.",
                    retryable=False,
                )

            last_result = result

            if result.success:
                return ToolExecution(
                    result=result,
                    attempts=attempt,
                )

            # Do not retry permanent or non-retryable errors
            if result.error is None or not result.error.retryable:
                return ToolExecution(
                    result=result,
                    attempts=attempt,
                )

            if attempt == self.retry_policy.max_attempts:
                break

            await asyncio.sleep(delay)

            delay = min(
                delay * self.retry_policy.backoff_multiplier,
                self.retry_policy.max_delay_seconds,
            )

        assert last_result is not None

        return ToolExecution(
            result=last_result,
            attempts=(self.retry_policy.max_attempts),
        )
