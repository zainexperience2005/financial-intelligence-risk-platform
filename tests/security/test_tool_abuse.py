"""Red-team security tests verifying tool abuse, repetition, and failure controls."""

from kit.loops.controller import LoopController
from kit.loops.models import LoopBudget, StopReason


def test_repeated_action_blocked_before_execution():
    """Identical tool calls beyond the repetition budget are blocked."""
    budget = LoopBudget(max_repeated_actions=2)
    controller = LoopController(budget=budget)

    controller.record_tool_call("fetch_policy", {"id": "POL-001"})
    assert controller.can_continue is True

    controller.record_tool_call("fetch_policy", {"id": "POL-001"})
    assert controller.can_continue is True

    controller.record_tool_call("fetch_policy", {"id": "POL-001"})
    assert controller.can_continue is False
    assert controller.status.stop_reason == StopReason.REPEATED_ACTION


def test_failure_budget_halts_tool_abuse():
    """Repeated tool execution failures halt the loop to prevent spamming backends."""
    budget = LoopBudget(max_failures=2)
    controller = LoopController(budget=budget)

    controller.record_failure()
    assert controller.can_continue is True

    controller.record_failure()
    assert controller.can_continue is True

    controller.record_failure()
    assert controller.can_continue is False
    assert controller.status.stop_reason == StopReason.TOO_MANY_FAILURES


def test_tool_call_budget_enforced():
    """Agents cannot exceed their configured global tool call budget."""
    budget = LoopBudget(max_tool_calls=3)
    controller = LoopController(budget=budget)

    controller.record_tool_call("tool_a", {"x": 1})
    assert controller.can_continue is True

    controller.record_tool_call("tool_b", {"x": 2})
    assert controller.can_continue is True

    controller.record_tool_call("tool_c", {"x": 3})
    assert controller.can_continue is True

    # 4th call is prohibited
    controller.record_tool_call("tool_d", {"x": 4})
    assert controller.can_continue is False
    assert controller.status.stop_reason == StopReason.MAX_TOOL_CALLS
