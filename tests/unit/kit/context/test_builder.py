import pytest

from kit.context.builder import ContextBudgetExceededError, ContextBuilder
from kit.context.estimator import estimate_tokens
from kit.context.models import (
    ContextBudget,
    ContextCategory,
    ContextItem,
)


def word_counter(text: str) -> int:
    return len(text.split())


def test_estimate_tokens():
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("abcdefgh") == 2
    assert estimate_tokens("hello world", counter=word_counter) == 2


def test_keeps_required_and_high_priority():
    builder = ContextBuilder(
        budget=ContextBudget(
            max_tokens=10,
            reserve_output_tokens=2,
        ),
        token_counter=word_counter,
    )

    items = [
        ContextItem(
            content="current user question",
            category=ContextCategory.CURRENT_REQUEST,
            priority=100,
            required=True,
        ),
        ContextItem(
            content="important policy evidence",
            category=ContextCategory.RETRIEVAL,
            priority=90,
        ),
        ContextItem(
            content="old conversation that is not important",
            category=ContextCategory.CONVERSATION,
            priority=20,
        ),
    ]

    result = builder.build(items)

    contents = [item.content for item in result.selected]

    assert "current user question" in contents
    assert "important policy evidence" in contents
    # Dropped low priority item due to budget constraint
    dropped_contents = [item.content for item in result.dropped]
    assert "old conversation that is not important" in dropped_contents


def test_required_context_overflow():
    builder = ContextBuilder(
        budget=ContextBudget(
            max_tokens=5,
            reserve_output_tokens=1,
        ),
        token_counter=word_counter,
    )

    items = [
        ContextItem(
            content="this required content is much too large",
            category=ContextCategory.CURRENT_REQUEST,
            required=True,
        )
    ]

    with pytest.raises(ContextBudgetExceededError):
        builder.build(items)


def test_no_available_context_budget():
    builder = ContextBuilder(
        budget=ContextBudget(
            max_tokens=10,
            reserve_output_tokens=10,
        ),
        token_counter=word_counter,
    )

    items = [
        ContextItem(
            content="hello",
            category=ContextCategory.CURRENT_REQUEST,
            required=True,
        )
    ]

    with pytest.raises(
        ContextBudgetExceededError,
        match="No input context budget available",
    ):
        builder.build(items)
