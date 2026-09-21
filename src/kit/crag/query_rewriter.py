from pydantic import BaseModel, Field

from kit.llms import create_chat_model
from kit.prompts import create_chat_prompt


class RewrittenQuery(BaseModel):
    query: str = Field(min_length=1)


SYSTEM_PROMPT = """
Rewrite a retrieval query so that it is more likely to find
relevant evidence in a knowledge base.

Preserve the user's original intent.

Do not answer the question.

Do not invent facts.

Return one focused retrieval query.
""".strip()


def rewrite_query(
    original_query: str,
    failure_reason: str,
) -> str:
    """Rewrites a weak or failing retrieval query to improve semantic search.

    Preserves the user's core intent without answering the question or
    hallucinating facts.
    """
    prompt = create_chat_prompt(
        system_prompt=SYSTEM_PROMPT,
        human_template=(
            "Original query:\n{query}\n\nWhy retrieval was weak:\n{reason}"
        ),
    )

    model = create_chat_model().with_structured_output(RewrittenQuery)

    chain = prompt | model

    result = chain.invoke(
        {
            "query": original_query,
            "reason": failure_reason,
        }
    )

    return result.query
