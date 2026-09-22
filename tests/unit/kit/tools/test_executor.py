import pytest

from kit.tools.exceptions import PermanentToolError, RetryableToolError
from kit.tools.executor import ControlledToolExecutor
from kit.tools.normalize import normalize_tool_result
from kit.tools.result import ToolResult
from kit.tools.retry import RetryPolicy


@pytest.mark.asyncio
async def test_retryable_failure_then_success():
    attempts = 0

    async def flaky_tool(arguments):
        nonlocal attempts
        attempts += 1

        if attempts < 3:
            return ToolResult.fail(
                code="TIMEOUT",
                message="Temporary timeout.",
                retryable=True,
            )

        return ToolResult.ok({"value": arguments["value"]})

    executor = ControlledToolExecutor(
        RetryPolicy(
            max_attempts=3,
            initial_delay_seconds=0,
        )
    )

    execution = await executor.execute(
        tool=flaky_tool,
        arguments={"value": 42},
    )

    assert execution.result.success
    assert execution.attempts == 3
    assert attempts == 3


@pytest.mark.asyncio
async def test_permanent_failure_not_retried():
    attempts = 0

    async def invalid_tool(arguments):
        nonlocal attempts
        attempts += 1

        return ToolResult.fail(
            code="INVALID_ARGUMENT",
            message="Invalid argument.",
            retryable=False,
        )

    executor = ControlledToolExecutor(
        RetryPolicy(
            max_attempts=5,
            initial_delay_seconds=0,
        )
    )

    execution = await executor.execute(
        tool=invalid_tool,
        arguments={},
    )

    assert not execution.result.success
    assert execution.attempts == 1
    assert attempts == 1


@pytest.mark.asyncio
async def test_retry_budget_exhausted():
    attempts = 0

    async def unavailable_tool(arguments):
        nonlocal attempts
        attempts += 1

        return ToolResult.fail(
            code="SERVICE_UNAVAILABLE",
            message="Service unavailable.",
            retryable=True,
        )

    executor = ControlledToolExecutor(
        RetryPolicy(
            max_attempts=3,
            initial_delay_seconds=0,
        )
    )

    execution = await executor.execute(
        tool=unavailable_tool,
        arguments={},
    )

    assert not execution.result.success
    assert execution.attempts == 3
    assert attempts == 3


@pytest.mark.asyncio
async def test_retryable_exception_retried():
    attempts = 0

    async def throwing_tool(arguments):
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise RetryableToolError("Transient network glitch")
        return ToolResult.ok({"status": "recovered"})

    executor = ControlledToolExecutor(
        RetryPolicy(
            max_attempts=3,
            initial_delay_seconds=0,
        )
    )

    execution = await executor.execute(tool=throwing_tool, arguments={})
    assert execution.result.success
    assert execution.attempts == 2
    assert attempts == 2


@pytest.mark.asyncio
async def test_permanent_exception_not_retried():
    attempts = 0

    async def failing_tool(arguments):
        nonlocal attempts
        attempts += 1
        raise PermanentToolError("SQL syntax error")

    executor = ControlledToolExecutor(
        RetryPolicy(
            max_attempts=3,
            initial_delay_seconds=0,
        )
    )

    execution = await executor.execute(tool=failing_tool, arguments={})
    assert not execution.result.success
    assert execution.result.error.code == "PERMANENT_TOOL_ERROR"
    assert execution.attempts == 1
    assert attempts == 1


@pytest.mark.asyncio
async def test_unexpected_exception_sanitized():
    async def crashing_tool(arguments):
        raise ValueError("postgres://user:secret_password@db.internal:5432/finance")

    executor = ControlledToolExecutor(
        RetryPolicy(
            max_attempts=3,
            initial_delay_seconds=0,
        )
    )

    execution = await executor.execute(tool=crashing_tool, arguments={})
    assert not execution.result.success
    assert execution.result.error.code == "INTERNAL_TOOL_ERROR"
    # Ensure sensitive credentials/paths from unexpected exceptions are not leaked
    assert "secret_password" not in execution.result.error.message
    assert execution.result.error.message == "Tool execution failed."
    assert not execution.result.error.retryable


def test_normalize_tool_result():
    existing = ToolResult.fail(code="ERR", message="fail")
    assert normalize_tool_result(existing) is existing

    raw_data = {"key": "val"}
    normalized = normalize_tool_result(raw_data)
    assert isinstance(normalized, ToolResult)
    assert normalized.success
    assert normalized.data == raw_data
