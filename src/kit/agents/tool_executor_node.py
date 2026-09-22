"""Controlled tool executor node for LangGraph agent graphs."""

from collections.abc import Callable, Sequence
from typing import Any

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import BaseTool

from kit.agents.react_state import ReActState
from kit.loops.controller import LoopController
from kit.loops.models import LoopBudget, LoopStatus
from kit.tools.executor import ControlledToolExecutor
from kit.tools.normalize import normalize_tool_result
from kit.tools.result import ToolResult
from kit.tools.retry import RetryPolicy


def create_tool_executor_node(
    tools: Sequence[BaseTool],
    *,
    default_budget: LoopBudget | None = None,
    retry_policy: RetryPolicy | None = None,
) -> Callable[[ReActState], Any]:
    """Create a LangGraph node that executes tool calls under ControlledToolExecutor.

    - Unknown tools immediately return machine-readable UNKNOWN_TOOL error
      and increment failure counts.
    - Transient errors are retried within tool execution according to RetryPolicy.
    - Permanent failures or exhausted retries record a single failed operation
    - Preserves original tool_call_id on emitted ToolMessages.
    - Serializes results as canonical JSON envelopes for consistent consumption.
    """
    budget = default_budget or LoopBudget()
    executor = ControlledToolExecutor(retry_policy=retry_policy)
    tools_by_name: dict[str, BaseTool] = {tool.name: tool for tool in tools}

    async def execute_tool_calls(state: ReActState) -> dict[str, Any]:
        controller = LoopController(
            budget=state.get("loop_budget", budget),
            status=state.get("loop_status", LoopStatus()),
        )

        message = state["messages"][-1]
        if not isinstance(message, AIMessage) or not message.tool_calls:
            return {"loop_status": controller.status}

        tool_messages: list[ToolMessage] = []

        for call in message.tool_calls:
            if not controller.can_continue:
                break

            tool_name = call["name"]
            tool_call_id = call.get("id") or ""
            arguments = call.get("args") or {}

            target_tool = tools_by_name.get(tool_name)
            if target_tool is None:
                controller.record_failure()
                fail_result = ToolResult.fail(
                    code="UNKNOWN_TOOL",
                    message="Requested tool is not available.",
                    retryable=False,
                )
                tool_messages.append(
                    ToolMessage(
                        tool_call_id=tool_call_id,
                        content=fail_result.model_dump_json(),
                    )
                )
                continue

            async def tool_callable(
                args: dict[str, Any],
                bound_tool: BaseTool = target_tool,
            ) -> ToolResult:
                raw = await bound_tool.ainvoke(args)
                return normalize_tool_result(raw)

            execution = await executor.execute(
                tool=tool_callable,
                arguments=arguments,
            )

            # Record failed tool operations to the agent-level budget
            if not execution.result.success:
                controller.record_failure()

            tool_messages.append(
                ToolMessage(
                    tool_call_id=tool_call_id,
                    content=execution.result.model_dump_json(),
                )
            )

        return {
            "messages": tool_messages,
            "loop_status": controller.status,
        }

    return execute_tool_calls
