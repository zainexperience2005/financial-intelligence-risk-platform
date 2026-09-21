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
