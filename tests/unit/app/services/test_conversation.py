from langchain_core.messages import AIMessage, HumanMessage

from app.services.conversation import MAX_RECENT_MESSAGES, format_recent_context


def test_format_recent_context_empty() -> None:
    assert format_recent_context([]) == ""


def test_format_recent_context_within_limit() -> None:
    messages = [
        HumanMessage(content="Investigate TX-1006"),
        AIMessage(content="Transaction TX-1006 flagged for review."),
    ]
    context = format_recent_context(messages)
    assert "human: Investigate TX-1006" in context
    assert "ai: Transaction TX-1006 flagged for review." in context


def test_format_recent_context_bounded_to_max() -> None:
    messages = [
        HumanMessage(content=f"Message {i}") for i in range(MAX_RECENT_MESSAGES + 5)
    ]
    context = format_recent_context(messages)
    lines = context.strip().split("\n")

    assert len(lines) == MAX_RECENT_MESSAGES
    # Should only contain the most recent messages
    assert f"Message {MAX_RECENT_MESSAGES + 4}" in lines[-1]
    assert "Message 0" not in context
