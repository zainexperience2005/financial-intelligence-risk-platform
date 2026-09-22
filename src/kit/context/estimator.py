"""Token estimation utilities and interfaces."""

from collections.abc import Callable

TokenCounter = Callable[[str], int]


def estimate_tokens(
    text: str,
    counter: TokenCounter | None = None,
) -> int:
    """Estimate token count for a string.

    Accepts an optional custom token counter (e.g. tiktoken).
    Defaults to heuristic fallback of ~4 characters per token.
    """
    if counter is not None:
        return counter(text)

    if not text:
        return 0

    return max(
        1,
        len(text) // 4,
    )
