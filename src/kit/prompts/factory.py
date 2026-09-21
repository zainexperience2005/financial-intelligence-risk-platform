from langchain_core.prompts import ChatPromptTemplate


def create_chat_prompt(
    system_prompt: str,
    human_template: str = "{input}",
) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", human_template),
        ]
    )
