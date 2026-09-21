from app.agents.financial_assistant import ask_financial_assistant
from app.graphs.state import FinancialState


def analyze_question(
    state: FinancialState,
) -> dict:
    question = state["question"]

    analysis = ask_financial_assistant(question)

    return {
        "analysis": analysis,
    }