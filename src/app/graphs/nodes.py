from app.agents.financial_assistant import ask_financial_assistant
from app.graphs.state import FinancialState
from app.agents.planner import create_investigation_plan

def analyze_question(
    state: FinancialState,
) -> dict:
    question = state["question"]

    analysis = ask_financial_assistant(question)

    return {
        "analysis": analysis,
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