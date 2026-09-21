from collections.abc import Sequence
from typing import Any

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.tools import BaseTool, tool

from kit.agents import AgentArchitecture, build_react_agent


class MockChatModel(FakeListChatModel):
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


def test_build_react_agent():
    model = MockChatModel(responses=["Done."])
    graph = build_react_agent(
        model=model,
        tools=[multiply],
        system_prompt="You are a helpful assistant.",
    )

    assert graph is not None
    assert "reason" in graph.nodes
    assert "tools" in graph.nodes
