from app.prompts import FINANCIAL_ASSISTANT_SYSTEM_PROMPT
from app.schemas import FinancialAnalysis
from kit.llms import create_chat_model
from kit.prompts import create_chat_prompt
from kit.security.pii import mask_free_text


def ask_financial_assistant(
    question: str,
) -> FinancialAnalysis:
    """
    Answers financial analysis questions using a language model.

    This function uses:
    - FINANCIAL_ASSISTANT_SYSTEM_PROMPT
    - Pydantic-based structured output
    - A simple chat chain without tools or external data access

    Returns:
        FinancialAnalysis
    """
    model = create_chat_model()

    structured_model = model.with_structured_output(FinancialAnalysis)

    prompt = create_chat_prompt(
        system_prompt=FINANCIAL_ASSISTANT_SYSTEM_PROMPT,
        human_template="{question}",
    )

    chain = prompt | structured_model

    result = chain.invoke(
        {
            "question": mask_free_text(question),
        }
    )

    return result
