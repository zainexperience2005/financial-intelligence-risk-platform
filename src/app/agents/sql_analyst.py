import json

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from app.agents.sql_loop import SQLLoopState
from app.prompts.sql_analyst import (
    SQL_ANALYST_SYSTEM_PROMPT,
)
from app.schemas import SQLAnalysisResult
from app.tools import (
    SafeSQLTool,
    SchemaInspectorTool,
)
from kit.llms import create_chat_model
from kit.tools.adapters import to_langchain_tool

MAX_TOOL_ITERATIONS = 6
MAX_SQL_ATTEMPTS = 3
MAX_REPEATED_QUERY_ATTEMPTS = 2


def run_sql_analyst(
    question: str,
) -> SQLAnalysisResult:
    loop_state = SQLLoopState()
    last_sql_result = None
    schema_tool = to_langchain_tool(SchemaInspectorTool())

    sql_tool = to_langchain_tool(SafeSQLTool())

    tools = [
        schema_tool,
        sql_tool,
    ]

    tools_by_name = {tool.name: tool for tool in tools}

    model = create_chat_model().bind_tools(tools)

    messages: list[BaseMessage] = [
        SystemMessage(content=SQL_ANALYST_SYSTEM_PROMPT),
        HumanMessage(content=question),
    ]

    for _ in range(MAX_TOOL_ITERATIONS):
        loop_state.iterations += 1
        response = model.invoke(messages)

        messages.append(response)

        if not isinstance(response, AIMessage) or not response.tool_calls:
            return SQLAnalysisResult(
                summary=str(response.content),
                sql_query=(last_sql_result.get("query") if last_sql_result else None),
                row_count=(
                    last_sql_result.get("row_count", 0) if last_sql_result else 0
                ),
                rows=(last_sql_result.get("rows", []) if last_sql_result else []),
                tool_iterations=loop_state.iterations,
                sql_attempts=loop_state.sql_attempts,
                failed_sql_attempts=(loop_state.failed_sql_attempts),
            )

        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            tool = tools_by_name.get(tool_name)

            if tool is None:
                observation = {
                    "success": False,
                    "error": (f"Unknown tool: {tool_name}"),
                }

            elif tool_name == "safe_sql":
                query = str(tool_args.get("query", "")).strip()

                repeated_count = loop_state.executed_queries.count(query)

                if repeated_count >= MAX_REPEATED_QUERY_ATTEMPTS:
                    observation = {
                        "success": False,
                        "error": (
                            "This SQL query has already been "
                            "attempted repeatedly. Inspect the "
                            "schema or try a different query."
                        ),
                    }

                    messages.append(
                        ToolMessage(
                            content=str(observation),
                            tool_call_id=tool_call.get("id") or "",
                        )
                    )

                    continue

                if loop_state.sql_attempts >= MAX_SQL_ATTEMPTS:
                    observation = {
                        "success": False,
                        "error": (
                            "SQL execution budget exhausted. "
                            "Do not execute another SQL query."
                        ),
                    }

                    messages.append(
                        ToolMessage(
                            content=str(observation),
                            tool_call_id=tool_call.get("id") or "",
                        )
                    )

                    continue

                loop_state.sql_attempts += 1

                loop_state.executed_queries.append(query)

                try:
                    observation = tool.invoke(tool_args)

                    if isinstance(observation, dict):
                        if observation.get("success"):
                            last_sql_result = observation.get("data")

                            loop_state.last_error = None

                        else:
                            loop_state.failed_sql_attempts += 1

                            loop_state.last_error = str(
                                observation.get(
                                    "error",
                                    "Unknown SQL error.",
                                )
                            )

                except Exception as exc:
                    loop_state.failed_sql_attempts += 1
                    loop_state.last_error = (
                        f"Tool execution failed: {type(exc).__name__}"
                    )
                    observation = {
                        "success": False,
                        "error": loop_state.last_error,
                    }

            else:
                try:
                    observation = tool.invoke(tool_args)

                except Exception as exc:
                    observation = {
                        "success": False,
                        "error": (f"Tool execution failed: {type(exc).__name__}"),
                    }

            content = (
                json.dumps(observation, default=str)
                if isinstance(observation, dict)
                else str(observation)
            )

            messages.append(
                ToolMessage(
                    content=content,
                    tool_call_id=tool_call.get("id") or "",
                )
            )

    return SQLAnalysisResult(
        summary=(
            "The SQL investigation stopped because "
            "the maximum number of tool iterations "
            "was reached."
        ),
        tool_iterations=loop_state.iterations,
        sql_attempts=loop_state.sql_attempts,
        failed_sql_attempts=(loop_state.failed_sql_attempts),
    )
