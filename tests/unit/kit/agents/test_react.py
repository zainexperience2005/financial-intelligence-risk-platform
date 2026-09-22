from collections.abc import Sequence
from typing import Any

import pytest
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import BaseTool, tool

from kit.agents import AgentArchitecture, build_react_agent
from kit.context.models import ContextBudget
from kit.llms.pricing import ModelPricing
from kit.llms.pricing_registry import PricingRegistry
from kit.llms.tracker import UsageTracker
from kit.loops.models import LoopBudget, LoopStatus, StopReason
from kit.tools.result import ToolResult
from kit.tools.retry import RetryPolicy


class MockChatModel(FakeMessagesListChatModel):
    def bind_tools(
        self,
        tools: Sequence[dict[str, Any] | type | Any | BaseTool],
        **kwargs: Any,
    ) -> Any:
        return self


@tool
def multiply(
    a: int,
    b: int,
) -> int:
    """Multiply two integers."""
    return a * b


def test_agent_architecture_enum():
    assert AgentArchitecture.REACT == "react"
    assert AgentArchitecture.PLANNER_EXECUTOR == "planner_executor"
    assert AgentArchitecture.HYBRID == "hybrid"


def test_build_react_agent_structure():
    model = MockChatModel(responses=[AIMessage(content="Done.")])
    graph = build_react_agent(
        model=model,
        tools=[multiply],
        system_prompt="You are a helpful assistant.",
    )

    assert graph is not None
    assert "agent" in graph.nodes
    assert "guard_tools" in graph.nodes
    assert "tools" in graph.nodes
    assert "complete" in graph.nodes


@pytest.mark.asyncio
async def test_react_scenario_a_final_answer():
    """Scenario A: Agent produces final answer directly -> COMPLETED."""
    model = MockChatModel(responses=[AIMessage(content="Final answer.")])
    agent = build_react_agent(
        model=model,
        tools=[multiply],
        system_prompt="You are a helpful assistant.",
    )

    result = await agent.ainvoke(
        {
            "messages": [HumanMessage(content="Hello")],
            "loop_budget": LoopBudget(),
            "loop_status": LoopStatus(),
        }
    )

    assert result["loop_status"].stopped is True
    assert result["loop_status"].stop_reason == StopReason.COMPLETED
    assert result["loop_status"].usage.iterations == 1
    assert result["loop_status"].usage.tool_calls == 0


@pytest.mark.asyncio
async def test_react_scenario_b_multiple_tools():
    """Scenario B: Agent -> tool A -> Agent -> tool B -> Agent -> final.
    Expected: iterations = 3, tool_calls = 2, COMPLETED.
    """
    calls = []

    @tool
    def tracked_echo(value: str) -> str:
        """Return the supplied value."""
        calls.append(value)
        return value

    responses = [
        AIMessage(
            content="",
            tool_calls=[
                {"name": "tracked_echo", "args": {"value": "first"}, "id": "call_1"}
            ],
        ),
        AIMessage(
            content="",
            tool_calls=[
                {"name": "tracked_echo", "args": {"value": "second"}, "id": "call_2"}
            ],
        ),
        AIMessage(content="All done."),
    ]

    model = MockChatModel(responses=responses)
    agent = build_react_agent(
        model=model,
        tools=[tracked_echo],
        system_prompt="You are a helpful assistant.",
    )

    result = await agent.ainvoke(
        {
            "messages": [HumanMessage(content="Run both tools.")],
            "loop_budget": LoopBudget(max_iterations=10, max_tool_calls=10),
            "loop_status": LoopStatus(),
        }
    )

    assert result["loop_status"].stopped is True
    assert result["loop_status"].stop_reason == StopReason.COMPLETED
    assert result["loop_status"].usage.iterations == 3
    assert result["loop_status"].usage.tool_calls == 2
    assert calls == ["first", "second"]


@pytest.mark.asyncio
async def test_react_scenario_c_repeated_action_guard():
    """Scenario C: Agent calls the same tool repeatedly.
    Expected: REPEATED_ACTION and third execution blocked.
    """
    calls = []

    @tool
    def tracked_echo(value: str) -> str:
        """Return the supplied value."""
        calls.append(value)
        return value

    # Agent repeatedly proposes the identical tool call
    responses = [
        AIMessage(
            content="",
            tool_calls=[
                {"name": "tracked_echo", "args": {"value": "hello"}, "id": "call_1"}
            ],
        ),
        AIMessage(
            content="",
            tool_calls=[
                {"name": "tracked_echo", "args": {"value": "hello"}, "id": "call_2"}
            ],
        ),
        AIMessage(
            content="",
            tool_calls=[
                {"name": "tracked_echo", "args": {"value": "hello"}, "id": "call_3"}
            ],
        ),
    ]

    model = MockChatModel(responses=responses)
    agent = build_react_agent(
        model=model,
        tools=[tracked_echo],
        system_prompt="You are a helpful assistant.",
    )

    result = await agent.ainvoke(
        {
            "messages": [HumanMessage(content="Echo hello repeatedly.")],
            "loop_budget": LoopBudget(
                max_iterations=6,
                max_tool_calls=8,
                max_failures=2,
                max_repeated_actions=2,
            ),
            "loop_status": LoopStatus(),
        }
    )

    assert result["loop_status"].stopped is True
    assert result["loop_status"].stop_reason == StopReason.REPEATED_ACTION
    # Crucial assertion: tool was only executed twice;
    # the third call was guarded and prevented before execution!
    assert calls == ["hello", "hello"]


@pytest.mark.asyncio
async def test_react_scenario_d_too_many_failures():
    """Scenario D: Agent requests failing operations repeatedly.
    Expected: TOO_MANY_FAILURES after exceeding max_failures budget.
    Model must not be called again after termination.
    """
    tool_invocations = []

    @tool
    def failing_tool(step: int) -> ToolResult:
        """Tool returning permanent failure."""
        tool_invocations.append(step)
        return ToolResult.fail(
            code="PERMANENT_ERROR",
            message=f"Step {step} permanently failed.",
            retryable=False,
        )

    responses = [
        AIMessage(
            content="",
            tool_calls=[{"name": "failing_tool", "args": {"step": 1}, "id": "call_1"}],
        ),
        AIMessage(
            content="",
            tool_calls=[{"name": "failing_tool", "args": {"step": 2}, "id": "call_2"}],
        ),
        AIMessage(
            content="",
            tool_calls=[{"name": "failing_tool", "args": {"step": 3}, "id": "call_3"}],
        ),
        AIMessage(content="Should never be reached"),
    ]

    model = MockChatModel(responses=responses)
    agent = build_react_agent(
        model=model,
        tools=[failing_tool],
        system_prompt="You are a helpful assistant.",
        retry_policy=RetryPolicy(max_attempts=1, initial_delay_seconds=0),
    )

    result = await agent.ainvoke(
        {
            "messages": [HumanMessage(content="Run steps")],
            "loop_budget": LoopBudget(
                max_iterations=10,
                max_tool_calls=10,
                max_failures=2,  # 3rd failure exceeds this budget
                max_repeated_actions=10,
            ),
            "loop_status": LoopStatus(),
        }
    )

    assert result["loop_status"].stopped is True
    assert result["loop_status"].stop_reason == StopReason.TOO_MANY_FAILURES
    assert result["loop_status"].usage.failures == 3
    assert tool_invocations == [1, 2, 3]
    # The 4th response was never consumed because the loop halted immediately at END
    assert model.i == 3


@pytest.mark.asyncio
async def test_react_unknown_tool_failure():
    """Unknown tool calls are treated as permanent failures and recorded on loop."""
    responses = [
        AIMessage(
            content="",
            tool_calls=[
                {"name": "non_existent_tool", "args": {}, "id": "call_unknown"}
            ],
        ),
        AIMessage(content="Recovered after error observation."),
    ]

    model = MockChatModel(responses=responses)
    agent = build_react_agent(
        model=model,
        tools=[multiply],
        system_prompt="You are a helpful assistant.",
    )

    result = await agent.ainvoke(
        {
            "messages": [HumanMessage(content="Call bad tool")],
            "loop_budget": LoopBudget(max_failures=3),
            "loop_status": LoopStatus(),
        }
    )

    assert result["loop_status"].usage.failures == 1
    assert result["loop_status"].stop_reason == StopReason.COMPLETED


@pytest.mark.asyncio
async def test_react_token_budget_prevents_tool_execution():
    """If an LLM call exhausts the token budget, requested tools MUST NOT execute."""
    calls = []

    @tool
    def tracked_tool(value: str) -> str:
        """Track tool invocation."""
        calls.append(value)
        return value

    response = AIMessage(
        content="",
        tool_calls=[
            {"name": "tracked_tool", "args": {"value": "run_me"}, "id": "call_1"}
        ],
        usage_metadata={
            "input_tokens": 700,
            "output_tokens": 400,
            "total_tokens": 1100,
        },
    )

    model = MockChatModel(responses=[response])
    agent = build_react_agent(
        model=model,
        tools=[tracked_tool],
        system_prompt="You are a helpful assistant.",
    )

    result = await agent.ainvoke(
        {
            "messages": [HumanMessage(content="Do task")],
            "loop_budget": LoopBudget(max_tokens=1000),
            "loop_status": LoopStatus(),
        }
    )

    assert result["loop_status"].stopped is True
    assert result["loop_status"].stop_reason == StopReason.TOKEN_BUDGET
    assert result["loop_status"].usage.total_tokens == 1100
    # Crucial assertion: requested tool call was prevented from executing
    assert calls == []


@pytest.mark.asyncio
async def test_react_cost_budget_prevents_tool_execution():
    """If an LLM call exhausts the cost budget, requested tools MUST NOT execute."""
    calls = []

    @tool
    def tracked_tool(value: str) -> str:
        """Track tool invocation."""
        calls.append(value)
        return value

    response = AIMessage(
        content="",
        tool_calls=[
            {"name": "tracked_tool", "args": {"value": "run_me"}, "id": "call_1"}
        ],
        usage_metadata={
            "input_tokens": 100_000,
            "output_tokens": 50_000,
            "total_tokens": 150_000,
        },
    )

    registry = PricingRegistry()
    registry.register(
        "custom-llm",
        ModelPricing(input_per_million=10.0, output_per_million=30.0),
    )
    tracker = UsageTracker(registry)

    model = MockChatModel(responses=[response])
    agent = build_react_agent(
        model=model,
        tools=[tracked_tool],
        system_prompt="You are a helpful assistant.",
        model_name="custom-llm",
        usage_tracker=tracker,
    )

    result = await agent.ainvoke(
        {
            "messages": [HumanMessage(content="Do task")],
            "loop_budget": LoopBudget(max_cost_usd=1.0),  # Call costs $2.50 > $1.0
            "loop_status": LoopStatus(),
        }
    )

    assert result["loop_status"].stopped is True
    assert result["loop_status"].stop_reason == StopReason.COST_BUDGET
    assert result["loop_status"].usage.estimated_cost_usd == 2.5
    # Crucial assertion: requested tool call was prevented from executing
    assert calls == []


@pytest.mark.asyncio
async def test_react_context_budget_exceeded():
    """If required context exceeds available context budget,
    terminates with CONTEXT_BUDGET.
    """
    model = MockChatModel(responses=[AIMessage(content="Should not be called")])
    agent = build_react_agent(
        model=model,
        tools=[multiply],
        system_prompt=(
            "A very long system prompt that will easily exceed "
            "the small context budget."
        ),
        context_budget=ContextBudget(max_tokens=10, reserve_output_tokens=5),
    )

    result = await agent.ainvoke(
        {
            "messages": [HumanMessage(content="Hello world from user")],
            "loop_budget": LoopBudget(),
            "loop_status": LoopStatus(),
        }
    )

    assert result["loop_status"].stopped is True
    assert result["loop_status"].stop_reason == StopReason.CONTEXT_BUDGET
    # Model was never invoked because budget was exceeded during context assembly
    assert model.i == 0
