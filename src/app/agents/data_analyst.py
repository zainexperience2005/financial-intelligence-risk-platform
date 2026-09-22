"""Data Analyst Agent for deterministic numeric calculations and aggregations.

Architecture Principle:
Database retrieval and data analysis are strictly separated:
- SQL Analyst retrieves authoritative structured rows.
- Data Analyst analyzes only explicitly supplied rows using deterministic
  Python/Pandas tools.
- Never asks an LLM to calculate arithmetic directly (avoids math hallucinations).
"""

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
from app.security.pii import prepare_model_evidence
from app.tools import ChartTool, DataAnalysisTool
from kit.charts.models import ChartArtifact
from kit.llms import create_chat_model
from kit.security.pii import mask_free_text
from kit.tools.adapters import to_langchain_tool

# Hard bound on tool invocations to ensure predictable latency and cost
MAX_ANALYTICS_TOOL_CALLS = 4


def run_data_analyst(
    question: str,
    rows: list[dict[str, Any]],
) -> DataAnalysisResult:
    """Runs the Data Analyst to perform calculations over retrieved rows.

    Args:
        question: The user's query or analytical objective.
        rows: Authoritative database rows retrieved by the SQL Analyst.

    Returns:
        DataAnalysisResult containing the summary, deterministic calculation output,
        and optional chart artifact.
    """
    analytics_tool = to_langchain_tool(DataAnalysisTool())
    chart_tool = to_langchain_tool(ChartTool())

    tools = [analytics_tool, chart_tool]
    model = create_chat_model().bind_tools(tools)

    safe_input = prepare_model_evidence({"question": question, "rows": rows})

    messages: list[BaseMessage] = [
        SystemMessage(content=DATA_ANALYST_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Question:\n{safe_input['question']}\n\n"
                f"Available rows:\n{safe_input['rows']}"
            )
        ),
    ]

    last_analysis = None
    last_chart: ChartArtifact | None = None
    tool_calls = 0

    for _ in range(MAX_ANALYTICS_TOOL_CALLS + 1):
        response = model.invoke(messages)

        messages.append(response)

        if not response.tool_calls:
            return DataAnalysisResult(
                summary=str(response.content),
                operation=(last_analysis["operation"] if last_analysis else None),
                result=(last_analysis["result"] if last_analysis else None),
                source_row_count=len(rows),
                chart=last_chart,
            )

        for tool_call in response.tool_calls:
            if tool_calls >= MAX_ANALYTICS_TOOL_CALLS:
                return DataAnalysisResult(
                    summary=("Analytics tool-call budget was exhausted."),
                    source_row_count=len(rows),
                    chart=last_chart,
                )

            tool_calls += 1

            tool_name = tool_call.get("name")
            if tool_name == "create_chart":
                target_tool = chart_tool
            else:
                target_tool = analytics_tool

            tool_args = dict(tool_call["args"])
            if tool_name != "create_chart":
                tool_args["rows"] = rows
            observation = target_tool.invoke(tool_args)

            if isinstance(observation, dict) and observation.get("success"):
                if tool_name == "create_chart":
                    try:
                        last_chart = ChartArtifact.model_validate(
                            observation.get("data")
                        )
                    except Exception:
                        pass
                else:
                    last_analysis = {
                        "operation": tool_call["args"].get("operation"),
                        "result": observation.get("data"),
                    }

            messages.append(
                ToolMessage(
                    content=mask_free_text(
                        str(
                            prepare_model_evidence(observation)
                            if isinstance(observation, dict)
                            else observation
                        )
                    ),
                    tool_call_id=tool_call["id"],
                )
            )

    return DataAnalysisResult(
        summary="Analytics execution stopped.",
        source_row_count=len(rows),
        chart=last_chart,
    )
