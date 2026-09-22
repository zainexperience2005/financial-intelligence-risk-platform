"""Defensive extraction of token usage from LangChain message metadata."""

from langchain_core.messages import AIMessage

from kit.llms.usage import TokenUsage


def extract_token_usage(
    message: AIMessage,
) -> TokenUsage:
    """Extract normalized input, output, and cached token metrics from an AIMessage."""
    usage = getattr(message, "usage_metadata", None) or {}

    input_tokens = int(
        usage.get(
            "input_tokens",
            0,
        )
    )

    output_tokens = int(
        usage.get(
            "output_tokens",
            0,
        )
    )

    input_details = (
        usage.get(
            "input_token_details",
            {},
        )
        or {}
    )

    cached_tokens = int(
        input_details.get(
            "cache_read",
            0,
        )
    )

    return TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_input_tokens=cached_tokens,
    )
