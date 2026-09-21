from app.prompts import PLANNER_SYSTEM_PROMPT
from app.schemas import InvestigationPlan
from kit.llms import create_chat_model
from kit.prompts import create_chat_prompt


def create_investigation_plan(
    question: str,
) -> InvestigationPlan:
    model = create_chat_model()

    structured_model = model.with_structured_output(InvestigationPlan)

    prompt = create_chat_prompt(
        system_prompt=PLANNER_SYSTEM_PROMPT,
        human_template="{question}",
    )

    chain = prompt | structured_model

    return chain.invoke(
        {
            "question": question,
        }
    )
