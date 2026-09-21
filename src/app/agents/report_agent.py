import json
from typing import Any

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)

from app.prompts.reports import (
    REPORT_SYSTEM_PROMPT,
)
from app.schemas import InvestigationReport
from kit.llms import create_chat_model


def create_investigation_report(
    evidence: dict[str, Any],
) -> InvestigationReport:
    model = create_chat_model().with_structured_output(InvestigationReport)

    messages = [
        SystemMessage(content=REPORT_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                "Create an investigation report "
                "from the following evidence:\n\n"
                + json.dumps(
                    evidence,
                    indent=2,
                    default=str,
                )
            )
        ),
    ]

    return model.invoke(messages)
