import asyncio

from langchain_core.messages import (
    HumanMessage,
)

from app.graphs.mcp_demo_graph import (
    build_mcp_demo_graph,
)
from app.mcp.server import mcp


async def main():
    graph = await build_mcp_demo_graph(mcp)
    result = await graph.ainvoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "Assess the risk of a "
                        "PKR 475000 failed "
                        "transaction with failure "
                        "reason risk_review, sent "
                        "from Pakistan to UAE."
                    )
                )
            ]
        }
    )
    print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
