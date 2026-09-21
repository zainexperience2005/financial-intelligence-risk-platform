from unittest.mock import patch

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from app.graphs.financial_graph import build_financial_graph
from app.schemas import InvestigationPlan
from app.schemas.report import InvestigationReport


def test_short_term_memory_across_turns_and_thread_isolation() -> None:
    checkpointer = MemorySaver()
    graph = build_financial_graph(checkpointer=checkpointer)

    fake_plan = InvestigationPlan(
        objective="Analyze question",
        requires_sql=False,
        requires_analytics=False,
        requires_policy=False,
        requires_risk=False,
        requires_action=False,
    )
    fake_report_turn_1 = InvestigationReport(
        executive_summary="Summary of Turn 1 for TX-1006.",
        findings=["Turn 1 Finding"],
        risk_summary="Turn 1 Risk.",
        recommendation="Review transaction.",
        evidence_sufficient=True,
    )
    fake_report_turn_2 = InvestigationReport(
        executive_summary="Summary of Turn 2 answering follow-up.",
        findings=["Turn 2 Finding"],
        risk_summary="Turn 2 Risk.",
        recommendation="Action recommended.",
        evidence_sufficient=True,
    )

    with (
        patch("app.graphs.nodes.create_investigation_plan", return_value=fake_plan),
        patch(
            "app.graphs.nodes.create_investigation_report",
            side_effect=[fake_report_turn_1, fake_report_turn_2, fake_report_turn_1],
        ),
    ):
        # Turn 1 on thread-1
        config_1 = {"configurable": {"thread_id": "test-thread-1"}}
        result_1 = graph.invoke(
            {
                "question": "Investigate TX-1006.",
                "messages": [HumanMessage(content="Investigate TX-1006.")],
            },
            config=config_1,
        )

        assert result_1["report"].executive_summary == "Summary of Turn 1 for TX-1006."
        # Messages should have HumanMessage + AIMessage
        assert len(result_1["messages"]) == 2
        assert result_1["messages"][0].content == "Investigate TX-1006."
        assert result_1["messages"][1].content == "Summary of Turn 1 for TX-1006."

        # Turn 2 on same thread-1
        result_2 = graph.invoke(
            {
                "question": "Why was it considered high risk?",
                "messages": [HumanMessage(content="Why was it considered high risk?")],
            },
            config=config_1,
        )

        # Messages should accumulate to 4 across turns
        assert len(result_2["messages"]) == 4
        assert result_2["messages"][2].content == "Why was it considered high risk?"
        assert (
            result_2["messages"][3].content == "Summary of Turn 2 answering follow-up."
        )

        # Thread isolation: invoke thread-2
        config_2 = {"configurable": {"thread_id": "test-thread-2"}}
        result_isolated = graph.invoke(
            {
                "question": "Independent question.",
                "messages": [HumanMessage(content="Independent question.")],
            },
            config=config_2,
        )

        # Thread 2 should only have 2 messages, completely isolated from thread-1
        assert len(result_isolated["messages"]) == 2
        assert result_isolated["messages"][0].content == "Independent question."
