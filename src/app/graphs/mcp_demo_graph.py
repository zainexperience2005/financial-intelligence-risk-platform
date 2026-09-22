from typing import Annotated, Any

from langchain_core.messages import (
    AnyMessage,
    SystemMessage,
)
from langgraph.graph import (
    END,
    START,
    StateGraph,
)
from langgraph.graph.message import (
    add_messages,
)
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from app.security.pii import prepare_model_text
from kit.llms import create_chat_model
from kit.mcp.client import MCPClient
from kit.mcp.langchain import (
    load_mcp_tools,
)


class MCPAgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


async def build_mcp_demo_graph(mcp_target: Any):
    client = MCPClient(mcp_target)
    tools = await load_mcp_tools(client)
    model = create_chat_model().bind_tools(tools)

    async def agent(state: MCPAgentState):
        messages = [
            SystemMessage(
                content=(
                    "You are a financial investigation assistant. "
                    "Use MCP tools when required. "
                    "Never invent tool results."
                )
            ),
            *(
                message.model_copy(
                    update={"content": prepare_model_text(message.content)}
                )
                if isinstance(message.content, str)
                else message
                for message in state["messages"]
            ),
        ]
        response = await model.ainvoke(messages)
        return {"messages": [response]}

    tool_node = ToolNode(tools)

    def route_after_agent(state: MCPAgentState):
        last_message = state["messages"][-1]
        if getattr(last_message, "tool_calls", None):
            return "tools"
        return END

    builder = StateGraph(MCPAgentState)
    builder.add_node("agent", agent)
    builder.add_node("tools", tool_node)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges(
        "agent",
        route_after_agent,
        {
            "tools": "tools",
            END: END,
        },
    )
    builder.add_edge("tools", "agent")

    return builder.compile()
