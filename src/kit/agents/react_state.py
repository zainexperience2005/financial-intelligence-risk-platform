"""TypedDict schema for serializable LangGraph ReAct agent state."""

from typing import Annotated

from langchain_core.messages import (
    AnyMessage,
)
from langgraph.graph.message import (
    add_messages,
)
from typing_extensions import TypedDict

from kit.loops.models import (
    LoopBudget,
    LoopStatus,
)


class ReActState(TypedDict):
    """LangGraph state representation for the loop-controlled ReAct agent.

    Maintains messages along with serializable Pydantic budget and status objects,
    guaranteeing clean serialization for database checkpointing (e.g. PostgresSaver).
    """

    messages: Annotated[
        list[AnyMessage],
        add_messages,
    ]

    loop_budget: LoopBudget

    loop_status: LoopStatus
