from sqlalchemy import text

from kit.databases import create_database_engine

engine = create_database_engine()


def database_is_healthy() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return True

    except Exception:
        return False
