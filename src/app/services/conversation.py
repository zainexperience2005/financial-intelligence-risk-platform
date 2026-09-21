from langchain_core.messages import (
    BaseMessage,
)

MAX_RECENT_MESSAGES = 6


def format_recent_context(
    messages: list[BaseMessage],
) -> str:
    recent = messages[-MAX_RECENT_MESSAGES:]

    parts: list[str] = []

    for message in recent:
        role = getattr(
            message,
            "type",
            "unknown",
        )

        parts.append(f"{role}: {message.content}")

    return "\n".join(parts)
