from sqlalchemy import Engine, create_engine

from kit.config import get_settings


def create_database_engine(
    database_url: str | None = None,
) -> Engine:
    settings = get_settings()

    url = database_url or settings.database_url

    return create_engine(
        url,
        pool_pre_ping=True,
    )