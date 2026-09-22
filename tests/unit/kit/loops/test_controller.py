from kit.loops.controller import LoopController
from kit.loops.models import LoopBudget, LoopStatus, StopReason


def test_controller_iteration_budget():
    controller = LoopController(budget=LoopBudget(max_iterations=2))
    assert controller.can_continue

    controller.start_iteration()  # 1
    assert controller.can_continue
    assert controller.status.usage.iterations == 1

    controller.start_iteration()  # 2
    assert controller.can_continue
    assert controller.status.usage.iterations == 2

    controller.start_iteration()  # 3 > 2
    assert not controller.can_continue
    assert controller.status.stopped is True
    assert controller.status.stop_reason == StopReason.MAX_ITERATIONS


def test_controller_tool_calls_budget():
    controller = LoopController(budget=LoopBudget(max_tool_calls=2))

    controller.record_tool_call("tool_a", {"x": 1})
    assert controller.can_continue

    controller.record_tool_call("tool_b", {"x": 2})
    assert controller.can_continue

    controller.record_tool_call("tool_c", {"x": 3})
    assert not controller.can_continue
    assert controller.status.stop_reason == StopReason.MAX_TOOL_CALLS


def test_controller_repeated_action_budget():
    controller = LoopController(budget=LoopBudget(max_repeated_actions=2))

    controller.record_tool_call("repeat_tool", {"arg": "val"})  # 1
    assert controller.can_continue

    controller.record_tool_call("repeat_tool", {"arg": "val"})  # 2
    assert controller.can_continue

    controller.record_tool_call("repeat_tool", {"arg": "val"})  # 3 > 2
    assert not controller.can_continue
    assert controller.status.stop_reason == StopReason.REPEATED_ACTION


def test_controller_failures_budget():
    controller = LoopController(budget=LoopBudget(max_failures=2))

    controller.record_failure()  # 1
    assert controller.can_continue

    controller.record_failure()  # 2
    assert controller.can_continue

    controller.record_failure()  # 3 > 2
    assert not controller.can_continue
    assert controller.status.stop_reason == StopReason.TOO_MANY_FAILURES


def test_controller_token_budget():
    controller = LoopController(budget=LoopBudget(max_tokens=100))

    controller.record_usage(tokens=50)
    assert controller.can_continue

    controller.record_usage(tokens=60)  # total 110 > 100
    assert not controller.can_continue
    assert controller.status.stop_reason == StopReason.TOKEN_BUDGET


def test_cumulative_token_budget():
    controller = LoopController(LoopBudget(max_tokens=1000))

    controller.record_usage(
        input_tokens=400,
        output_tokens=100,
        cost_usd=0.01,
    )
    assert controller.can_continue

    controller.record_usage(
        input_tokens=450,
        output_tokens=100,
        cost_usd=0.01,
    )
    assert not controller.can_continue
    assert controller.status.stop_reason == StopReason.TOKEN_BUDGET
    assert controller.status.usage.input_tokens == 850
    assert controller.status.usage.output_tokens == 200
    assert controller.status.usage.total_tokens == 1050


def test_controller_cost_budget():
    controller = LoopController(budget=LoopBudget(max_cost_usd=0.05))

    controller.record_usage(cost_usd=0.02)
    assert controller.can_continue

    controller.record_usage(cost_usd=0.04)  # total 0.06 > 0.05
    assert not controller.can_continue
    assert controller.status.stop_reason == StopReason.COST_BUDGET


def test_unknown_cost_stops_when_budgeted():
    controller = LoopController(LoopBudget(max_cost_usd=0.10))

    controller.record_usage(
        input_tokens=100,
        output_tokens=50,
        cost_usd=None,
    )

    assert not controller.can_continue
    assert controller.status.stop_reason == StopReason.UNKNOWN_COST


def test_unknown_cost_allowed_without_cost_budget():
    controller = LoopController(LoopBudget(max_cost_usd=None))

    controller.record_usage(
        input_tokens=100,
        output_tokens=50,
        cost_usd=None,
    )

    assert controller.can_continue
    assert not controller.status.usage.cost_complete


def test_controller_completion():
    controller = LoopController()
    controller.complete()
    assert not controller.can_continue
    assert controller.status.stopped is True
    assert controller.status.stop_reason == StopReason.COMPLETED


def test_controller_restoration():
    status = LoopStatus()
    status.usage.iterations = 2
    budget = LoopBudget(max_iterations=3)

    controller = LoopController(budget=budget, status=status)
    assert controller.status.usage.iterations == 2

    controller.start_iteration()  # 3
    assert controller.can_continue

    controller.start_iteration()  # 4 > 3
    assert not controller.can_continue
    assert controller.status.stop_reason == StopReason.MAX_ITERATIONS
