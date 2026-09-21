from langgraph.checkpoint.postgres import (
    PostgresSaver,
)

from kit.config import get_settings


def create_postgres_checkpointer():
    settings = get_settings()

    return PostgresSaver.from_conn_string(settings.checkpoint_database_url)
