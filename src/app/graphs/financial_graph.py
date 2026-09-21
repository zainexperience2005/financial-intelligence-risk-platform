from langgraph.graph import END, START, StateGraph

from app.graphs.nodes import analyze_question
from app.graphs.state import FinancialState


def build_financial_graph():
    builder = StateGraph(FinancialState)

    builder.add_node(
        "analyze",
        analyze_question,
    )

    builder.add_edge(
        START,
        "analyze",
    )

    builder.add_edge(
        "analyze",
        END,
    )

    return builder.compile()