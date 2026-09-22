"""Security tests verifying iteration, spend, token, and context resource limits."""

import pytest

from kit.context.builder import ContextBudgetExceededError, ContextBuilder
from kit.context.models import ContextBudget, ContextCategory, ContextItem
from kit.loops.controller import LoopController
from kit.loops.models import LoopBudget, StopReason


def test_iteration_budget_ceiling():
    """Reasoning loops cannot exceed maximum iteration limit."""
    budget = LoopBudget(max_iterations=3)
    controller = LoopController(budget=budget)

    controller.start_iteration()  # 1
    assert controller.can_continue is True
    controller.start_iteration()  # 2
    assert controller.can_continue is True
    controller.start_iteration()  # 3
    assert controller.can_continue is True
    controller.start_iteration()  # 4 -> EXCEEDED
    assert controller.can_continue is False
    assert controller.status.stop_reason == StopReason.MAX_ITERATIONS


def test_token_budget_ceiling():
    """Cumulative token consumption stops the agent at the configured ceiling."""
    budget = LoopBudget(max_tokens=1000)
    controller = LoopController(budget=budget)

    controller.record_usage(input_tokens=600, output_tokens=200, cost_usd=0.01)
    assert controller.can_continue is True

    # Exceed budget
    controller.record_usage(input_tokens=250, output_tokens=100, cost_usd=0.01)
    assert controller.can_continue is False
    assert controller.status.stop_reason == StopReason.TOKEN_BUDGET


def test_cost_budget_ceiling():
    """Cumulative financial spend stops execution at the dollar ceiling."""
    budget = LoopBudget(max_cost_usd=0.05)
    controller = LoopController(budget=budget)

    controller.record_usage(input_tokens=1000, output_tokens=500, cost_usd=0.03)
    assert controller.can_continue is True

    controller.record_usage(input_tokens=1000, output_tokens=500, cost_usd=0.03)
    assert controller.can_continue is False
    assert controller.status.stop_reason == StopReason.COST_BUDGET


def test_cost_budget_fails_closed_on_unpriced_call():
    """When a cost budget is enforced, unpriced model calls must fail closed."""
    budget = LoopBudget(max_cost_usd=0.10)
    controller = LoopController(budget=budget)

    # Cost is None
    controller.record_usage(input_tokens=100, output_tokens=50, cost_usd=None)
    assert controller.can_continue is False
    assert controller.status.stop_reason == StopReason.UNKNOWN_COST


def test_context_budget_flooding_blocked():
    """ContextBuilder blocks prompt flooding when required context exceeds capacity."""
    # Small budget: 50 tokens available for input
    budget = ContextBudget(max_tokens=100, reserve_output_tokens=50)
    builder = ContextBuilder(budget=budget)

    # Required payload is 500 characters (~125 tokens)
    enormous_input = "CRITICAL REQUIRED FACT " * 50
    items = [
        ContextItem(
            content=enormous_input,
            category=ContextCategory.SYSTEM,
            priority=100,
            required=True,
        )
    ]

    with pytest.raises(ContextBudgetExceededError):
        builder.build(items)
