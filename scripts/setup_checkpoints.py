from __future__ import annotations

import sys
from pathlib import Path

_src = str(Path(__file__).resolve().parent.parent / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from langgraph.checkpoint.postgres import (
    PostgresSaver,
)

from kit.config import get_settings


def main() -> None:
    settings = get_settings()

    with PostgresSaver.from_conn_string(
        settings.checkpoint_database_url
    ) as checkpointer:
        checkpointer.setup()

    print("LangGraph checkpoint tables ready.")


if __name__ == "__main__":
    main()
