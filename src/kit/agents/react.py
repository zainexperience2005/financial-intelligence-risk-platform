from collections.abc import Sequence
from typing import Annotated

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AnyMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict


class ReActState(TypedDict):
    messages: Annotated[
        list[AnyMessage],
        add_messages,
    ]


def build_react_agent(
    *,
    model: BaseChatModel,
    tools: Sequence[BaseTool],
    system_prompt: str,
):
    bound_model = model.bind_tools(list(tools))

    async def reason(state: ReActState):
        messages = [
            SystemMessage(content=system_prompt),
            *state["messages"],
        ]
        response = await bound_model.ainvoke(messages)
        return {"messages": [response]}

    tool_node = ToolNode(list(tools))

    def route(state: ReActState):
        last_message = state["messages"][-1]
        if getattr(last_message, "tool_calls", None):
            return "tools"
        return END

    builder = StateGraph(ReActState)
    builder.add_node("reason", reason)
    builder.add_node("tools", tool_node)

    builder.add_edge(START, "reason")
    builder.add_conditional_edges(
        "reason",
        route,
        {
            "tools": "tools",
            END: END,
        },
    )
    builder.add_edge("tools", "reason")

    return builder.compile()
