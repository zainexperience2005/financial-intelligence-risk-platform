"""Financial Intelligence & Risk Platform Multi-Agent StateGraph.

Orchestration Workflow:
START -> planner
           ├── requires_sql -> sql_analyst
           │     ├── requires_analytics -> data_analyst
           │     │     ├── requires_policy -> policy_agent -> analyze
           │     │     └── no policy -> analyze
           │     ├── requires_policy -> policy_agent -> analyze
           │     └── no analytics/policy -> analyze
           └── direct inquiry -> analyze
                                  ├── requires_data -> data_required -> END
                                  └── complete -> END
"""

from langgraph.graph import END, START, StateGraph

from app.graphs.nodes import (
    analyze_data,
    analyze_policy,
    analyze_question,
    analyze_sql,
    handle_data_requirement,
    plan_investigation,
)
from app.graphs.router import (
    route_after_analysis,
    route_after_analytics,
    route_after_planning,
    route_after_sql,
)
from app.graphs.state import FinancialState


def build_financial_graph():
    """Builds and compiles the multi-agent investigation graph."""
    builder = StateGraph(FinancialState)  # type: ignore[arg-type]

    builder.add_node(
        "planner",
        plan_investigation,
    )

    builder.add_node(
        "sql_analyst",
        analyze_sql,
    )

    builder.add_node(
        "data_analyst",
        analyze_data,
    )

    builder.add_node(
        "policy_agent",
        analyze_policy,
    )

    builder.add_node(
        "analyze",
        analyze_question,
    )

    builder.add_node(
        "data_required",
        handle_data_requirement,
    )

    builder.add_edge(
        START,
        "planner",
    )

    builder.add_conditional_edges(
        "planner",
        route_after_planning,
        {
            "sql": "sql_analyst",
            "analyze": "analyze",
        },
    )

    builder.add_conditional_edges(
        "sql_analyst",
        route_after_sql,
        {
            "analytics": "data_analyst",
            "policy": "policy_agent",
            "analyze": "analyze",
        },
    )

    builder.add_conditional_edges(
        "data_analyst",
        route_after_analytics,
        {
            "policy": "policy_agent",
            "analyze": "analyze",
        },
    )

    builder.add_edge(
        "policy_agent",
        "analyze",
    )

    builder.add_conditional_edges(
        "analyze",
        route_after_analysis,
        {
            "data_required": "data_required",
            "complete": END,
        },
    )

    builder.add_edge(
        "data_required",
        END,
    )

    return builder.compile()
