from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from kit.databases.engine import create_database_engine

engine = create_database_engine()


def create_session_factory(
    engine,
) -> sessionmaker[Session]:
    return sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )


SessionFactory = create_session_factory(engine)


def get_database_session() -> Generator[Session, None, None]:
    session = SessionFactory()

    try:
        yield session
    finally:
        session.close()
