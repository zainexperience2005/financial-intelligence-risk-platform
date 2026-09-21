from app.graphs.financial_graph import build_financial_graph


def test_financial_graph_builds_and_contains_all_nodes():
    graph = build_financial_graph()

    expected_nodes = {
        "__start__",
        "planner",
        "sql_analyst",
        "data_analyst",
        "policy_agent",
        "analyze",
        "data_required",
    }

    assert expected_nodes.issubset(set(graph.nodes.keys()))


def test_financial_graph_has_valid_edges():
    graph = build_financial_graph()

    # Verify key direct edges exist
    edges = set(graph.builder.edges)
    assert ("__start__", "planner") in edges
    assert ("policy_agent", "analyze") in edges
    assert ("data_required", "__end__") in edges
