from app.agents.data_analyst import run_data_analyst
from app.agents.financial_assistant import ask_financial_assistant
from app.agents.planner import create_investigation_plan
from app.agents.policy_agent import (
    run_policy_agent,
)
from app.agents.sql_analyst import run_sql_analyst
from app.graphs.state import FinancialState


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
    question = state["question"]

    plan = create_investigation_plan(question)

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
