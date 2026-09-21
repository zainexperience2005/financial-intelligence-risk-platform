from langchain_core.messages import AIMessage

from app.agents.data_analyst import run_data_analyst
from app.agents.financial_assistant import ask_financial_assistant
from app.agents.planner import create_investigation_plan
from app.agents.policy_agent import (
    run_policy_agent,
)
from app.agents.report_agent import create_investigation_report
from app.agents.risk_agent import run_risk_agent
from app.agents.sql_analyst import run_sql_analyst
from app.graphs.dependencies import normalize_plan
from app.graphs.state import FinancialState
from app.services.conversation import format_recent_context
from app.services.evidence import build_evidence_bundle


def prepare_turn(
    state: FinancialState,
) -> dict:
    """Resets turn-scoped specialist evidence while preserving thread messages."""
    return {
        "plan": None,
        "sql_analysis": None,
        "data_analysis": None,
        "policy_analysis": None,
        "risk_analysis": None,
        "report": None,
    }


def analyze_question(
    state: FinancialState,
) -> dict:
    question = state["question"]

    analysis = ask_financial_assistant(question)

    return {
        "analysis": analysis,
    }


def analyze_sql(
    state: FinancialState,
) -> dict:
    result = run_sql_analyst(state["question"])

    return {
        "sql_analysis": result,
    }


def handle_data_requirement(
    state: FinancialState,
) -> dict:
    return {
        "data_required": True,
        "data_message": (
            "This investigation requires access to "
            "financial data. Data tools are not yet "
            "connected."
        ),
    }


def plan_investigation(
    state: FinancialState,
) -> dict:
    context = format_recent_context(state.get("messages", []))

    plan = create_investigation_plan(
        question=state["question"],
        conversation_context=context,
    )
    plan = normalize_plan(plan)

    return {
        "plan": plan,
    }


def analyze_data(
    state: FinancialState,
) -> dict:
    sql_analysis = state.get("sql_analysis")

    if sql_analysis is None:
        return {}

    result = run_data_analyst(
        question=state["question"],
        rows=sql_analysis.rows,
    )

    return {
        "data_analysis": result,
    }


def analyze_policy(
    state: FinancialState,
) -> dict:
    result = run_policy_agent(state["question"])

    return {
        "policy_analysis": result,
    }


def analyze_risk(
    state: FinancialState,
) -> dict:
    sql_analysis = state.get("sql_analysis")

    if sql_analysis is None or not sql_analysis.rows:
        return {}

    # Risk analysis requires a single unambiguous transaction.
    # When multiple rows are returned the investigation is not scoped to one
    # transaction, so we cannot produce a valid deterministic risk score.
    if len(sql_analysis.rows) > 1:
        return {}

    transaction = sql_analysis.rows[0]

    customer_country = transaction.get("customer_country")

    result = run_risk_agent(
        transaction=transaction,
        customer_country=customer_country,
        policy_analysis=state.get("policy_analysis"),
    )

    return {
        "risk_analysis": result,
    }


def create_report(
    state: FinancialState,
) -> dict:
    evidence = build_evidence_bundle(state)

    report = create_investigation_report(evidence)

    return {
        "report": report,
        "messages": [
            AIMessage(
                content=report.executive_summary,
            )
        ],
    }
