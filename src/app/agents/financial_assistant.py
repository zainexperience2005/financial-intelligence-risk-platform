from langchain_core.messages import HumanMessage, SystemMessage

from kit.llms import create_chat_model

SYSTEM_PROMPT = """
You are a financial intelligence assistant.

Your current responsibility is only to answer general
financial-analysis questions.

Do not claim to have queried databases, policies, transactions,
or external systems unless such capabilities are explicitly
provided to you.
"""


def ask_financial_assistant(question: str) -> str:
    """
    Asks the financial assistant a question and returns the response.
    """
    model = create_chat_model()

    response = model.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=question),
        ]
    )

    return str(response.content)