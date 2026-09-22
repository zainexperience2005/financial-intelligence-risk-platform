"""Deterministic action signature generation for loop repetition detection."""

import hashlib
import json
from typing import Any


def create_action_signature(
    action_name: str,
    arguments: dict[str, Any],
) -> str:
    """Create a deterministic SHA-256 signature for a tool name and arguments.

    Used by the LoopController to detect repeated tool executions before they run.
    Arguments are sorted and serialized canonically to guarantee identical hashes
    regardless of key insertion order.
    """
    payload = {
        "action": action_name,
        "arguments": arguments,
    }

    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )

    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
