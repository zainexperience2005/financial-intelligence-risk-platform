"""Defense-in-depth checks for the model-facing PostgreSQL role."""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from kit.config import get_settings

pytestmark = [pytest.mark.integration, pytest.mark.postgres]


@pytest.fixture
def reader_engine():
    url = get_settings().read_only_database_url
    if url.startswith("sqlite"):
        pytest.skip("requires an explicitly configured PostgreSQL reader role")
    engine = create_engine(url)
    yield engine
    engine.dispose()


def test_financial_reader_can_select(reader_engine) -> None:
    with reader_engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1
        connection.execute(text("SELECT * FROM accounts LIMIT 1")).all()


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE accounts SET status = status",
        "DELETE FROM accounts",
        "INSERT INTO accounts DEFAULT VALUES",
        "DROP TABLE accounts",
    ],
)
def test_financial_reader_cannot_mutate_or_drop(reader_engine, statement: str) -> None:
    with reader_engine.connect() as connection:
        with pytest.raises(DBAPIError):
            connection.execute(text(statement))
        connection.rollback()
