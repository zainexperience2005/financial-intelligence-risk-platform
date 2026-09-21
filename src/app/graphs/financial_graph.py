from langgraph.graph import END, START, StateGraph

from app.graphs.nodes import (
    analyze_question,
    handle_data_requirement,
    plan_investigation,
)
from app.graphs.router import route_after_analysis
from app.graphs.state import FinancialState


def build_financial_graph():
    builder = StateGraph(FinancialState)

    builder.add_node(
        "planner",
        plan_investigation,
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

    builder.add_edge(
        "planner",
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