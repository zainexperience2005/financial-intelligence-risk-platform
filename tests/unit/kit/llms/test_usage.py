from langchain_core.messages import AIMessage

from kit.llms.pricing import ModelPricing, calculate_cost
from kit.llms.pricing_registry import PricingRegistry
from kit.llms.tracker import UsageTracker
from kit.llms.usage_extractor import extract_token_usage


def test_extract_usage():
    message = AIMessage(
        content="Done",
        usage_metadata={
            "input_tokens": 800,
            "output_tokens": 200,
            "total_tokens": 1000,
        },
    )

    usage = extract_token_usage(message)

    assert usage.input_tokens == 800
    assert usage.output_tokens == 200
    assert usage.total_tokens == 1000


def test_calculate_cost():
    pricing = ModelPricing(
        input_per_million=2.0,
        output_per_million=8.0,
    )

    cost = calculate_cost(
        input_tokens=1_000_000,
        output_tokens=500_000,
        cached_input_tokens=0,
        pricing=pricing,
    )

    assert cost == 6.0


def test_calculate_cost_with_cached_input():
    pricing = ModelPricing(
        input_per_million=2.0,
        output_per_million=8.0,
        cached_input_per_million=0.5,
    )

    cost = calculate_cost(
        input_tokens=1_000_000,
        output_tokens=500_000,
        cached_input_tokens=600_000,
        pricing=pricing,
    )

    assert round(cost, 4) == 5.1


def test_usage_tracker_known_pricing():
    registry = PricingRegistry()
    registry.register(
        "test-model",
        ModelPricing(input_per_million=10.0, output_per_million=30.0),
    )
    tracker = UsageTracker(registry)

    message = AIMessage(
        content="Result",
        usage_metadata={
            "input_tokens": 100_000,
            "output_tokens": 50_000,
            "total_tokens": 150_000,
        },
    )

    usage = tracker.track(model="test-model", message=message)
    assert usage.tokens.input_tokens == 100_000
    assert usage.tokens.output_tokens == 50_000
    # 0.1M * 10 = $1.0 + 0.05M * 30 = $1.5 => $2.5
    assert usage.estimated_cost_usd == 2.5


def test_usage_tracker_unknown_pricing():
    registry = PricingRegistry()
    tracker = UsageTracker(registry)

    message = AIMessage(
        content="Result",
        usage_metadata={
            "input_tokens": 100,
            "output_tokens": 50,
            "total_tokens": 150,
        },
    )

    usage = tracker.track(model="unregistered-model", message=message)
    assert usage.tokens.total_tokens == 150
    # Unknown price must never be reported as $0.00
    assert usage.estimated_cost_usd is None
