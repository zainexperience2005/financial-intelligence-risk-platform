from app.graphs.financial_graph import build_financial_graph


def test_financial_graph_builds_and_contains_all_nodes():
    graph = build_financial_graph()

    expected_nodes = {
        "__start__",
        "prepare_turn",
        "planner",
        "sql_analyst",
        "data_analyst",
        "policy_agent",
        "risk_agent",
        "report",
        "analyze",
        "data_required",
    }

    assert expected_nodes.issubset(set(graph.nodes.keys()))


def test_financial_graph_has_valid_edges():
    graph = build_financial_graph()

    # Verify key direct edges exist
    edges = set(graph.builder.edges)
    assert ("__start__", "prepare_turn") in edges
    assert ("prepare_turn", "planner") in edges
    assert ("risk_agent", "report") in edges
    assert ("report", "__end__") in edges
    assert ("data_required", "__end__") in edges
