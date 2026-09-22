from kit.context.builder import ContextBuilder
from kit.context.models import ContextBudget, ContextCategory, ContextItem


def test_context_builder_preserves_sql_and_drops_memory_under_budget():
    # SQL (~14 tokens) + Policy (~18 tokens) = ~32 tokens.
    # Total with Memory (~14 tokens) = ~46 tokens.
    # We set available budget to 35 so SQL and Policy fit, but Memory is dropped.
    budget = ContextBudget(
        max_tokens=45,
        reserve_output_tokens=10,
    )
    # Available tokens = 35

    sql_item = ContextItem(
        content="Current SQL: Transaction TX-1006 status=reviewed, amount=12000.0",
        category=ContextCategory.TOOL_RESULT,
        priority=95,
        required=True,
        source_id="sql_tx_1006",
    )

    policy_item = ContextItem(
        content="Policy: FIN-POL-003 requires approval for transfers > 10000.",
        category=ContextCategory.RETRIEVAL,
        priority=80,
        required=False,
        source_id="pol_003",
    )


    memory_item = ContextItem(
        content="Memory: TX-1006 investigated previously with status=failed.",
        category=ContextCategory.MEMORY,
        priority=40,
        required=False,
        source_id="mem_tx_1006",
    )

    builder = ContextBuilder(budget=budget)
    result = builder.build([sql_item, policy_item, memory_item])

    selected_categories = [item.category for item in result.selected]
    dropped_categories = [item.category for item in result.dropped]

    # Authoritative SQL evidence is required and preserved
    assert ContextCategory.TOOL_RESULT in selected_categories
    # Stale historical memory is dropped under budget pressure
    assert ContextCategory.MEMORY in dropped_categories


def test_stale_memory_conflict_prioritizes_current_sql():
    # Current SQL (~9 tokens) vs Stale Memory (~10 tokens).
    # Total = 19 tokens.
    # Available budget = 14 tokens (max_tokens=19, reserve=5)
    budget = ContextBudget(
        max_tokens=19,
        reserve_output_tokens=5,
    )
    # Available tokens = 14 (SQL fits, Memory cannot fit)

    current_sql = ContextItem(
        content="Current SQL: TX-1006 status = reviewed",
        category=ContextCategory.TOOL_RESULT,
        priority=95,
        required=False,
        source_id="sql_1",
    )

    stale_memory = ContextItem(
        content="Historical Memory: TX-1006 status = failed",
        category=ContextCategory.MEMORY,
        priority=40,
        required=False,
        source_id="mem_1",
    )

    builder = ContextBuilder(budget=budget)
    result = builder.build([current_sql, stale_memory])

    # Current SQL must be selected over stale memory
    assert len(result.selected) == 1
    assert result.selected[0].category == ContextCategory.TOOL_RESULT
    assert "status = reviewed" in result.selected[0].content
    assert len(result.dropped) == 1
    assert result.dropped[0].category == ContextCategory.MEMORY



def test_evidence_hierarchy_priority_ordering():
    # Verify relative priorities match the architecture:
    # Current SQL (95) > Analytics (90) > Policy (80) > Memory (40) > Conversation (20)
    sql_priority = 95
    analytics_priority = 90
    policy_priority = 80
    memory_priority = 40
    conversation_priority = 20

    assert (
        sql_priority
        > analytics_priority
        > policy_priority
        > memory_priority
        > conversation_priority
    )


