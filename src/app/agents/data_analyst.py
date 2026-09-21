from typing import Any

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from app.prompts.data_analyst import (
    DATA_ANALYST_SYSTEM_PROMPT,
)
from app.schemas import DataAnalysisResult
from app.tools import DataAnalysisTool
from kit.llms import create_chat_model
from kit.tools.adapters import to_langchain_tool


MAX_ANALYTICS_TOOL_CALLS = 3


def run_data_analyst(
    question: str,
    rows: list[dict[str, Any]],
) -> DataAnalysisResult:
    analytics_tool = to_langchain_tool(
        DataAnalysisTool()
    )

    model = create_chat_model().bind_tools(
        [analytics_tool]
    )

    messages: list[BaseMessage] = [
        SystemMessage(
            content=DATA_ANALYST_SYSTEM_PROMPT
        ),
        HumanMessage(
            content=(
                f"Question:\n{question}\n\n"
                f"Available rows:\n{rows}"
            )
        ),
    ]

    last_analysis = None
    tool_calls = 0

    for _ in range(MAX_ANALYTICS_TOOL_CALLS + 1):
        response = model.invoke(messages)

        messages.append(response)

        if not response.tool_calls:
            return DataAnalysisResult(
                summary=str(response.content),
                operation=(
                    last_analysis["operation"]
                    if last_analysis
                    else None
                ),
                result=(
                    last_analysis["result"]
                    if last_analysis
                    else None
                ),
                source_row_count=len(rows),
            )

        for tool_call in response.tool_calls:
            if tool_calls >= MAX_ANALYTICS_TOOL_CALLS:
                return DataAnalysisResult(
                    summary=(
                        "Analytics tool-call budget "
                        "was exhausted."
                    ),
                    source_row_count=len(rows),
                )

            tool_calls += 1

            observation = analytics_tool.invoke(
                tool_call["args"]
            )

            if (
                isinstance(observation, dict)
                and observation.get("success")
            ):
                last_analysis = {
                    "operation": tool_call["args"].get(
                        "operation"
                    ),
                    "result": observation.get("data"),
                }

            messages.append(
                ToolMessage(
                    content=str(observation),
                    tool_call_id=tool_call["id"],
                )
            )

    return DataAnalysisResult(
        summary="Analytics execution stopped.",
        source_row_count=len(rows),
    )