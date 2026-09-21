from collections.abc import Callable
from typing import Any

GraphNode = Callable[
    [dict[str, Any]],
    dict[str, Any],
]
