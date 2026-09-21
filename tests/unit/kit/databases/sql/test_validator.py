import pytest

from kit.databases.sql import (
    SQLValidationError,
    apply_row_limit,
    validate_read_only_sql,
)


def test_select_is_allowed() -> None:
    statement = validate_read_only_sql("SELECT * FROM transactions")

    assert statement is not None


def test_delete_is_rejected() -> None:
    with pytest.raises(SQLValidationError):
        validate_read_only_sql("DELETE FROM transactions")


def test_update_is_rejected() -> None:
    with pytest.raises(SQLValidationError):
        validate_read_only_sql(
            """
            UPDATE transactions
            SET status = 'completed'
            """
        )


def test_drop_is_rejected() -> None:
    with pytest.raises(SQLValidationError):
        validate_read_only_sql("DROP TABLE transactions")


def test_multiple_statements_are_rejected() -> None:
    with pytest.raises(SQLValidationError):
        validate_read_only_sql(
            """
            SELECT * FROM transactions;
            DROP TABLE transactions;
            """
        )


def test_limit_is_added() -> None:
    statement = validate_read_only_sql("SELECT * FROM transactions")

    sql = apply_row_limit(
        statement,
        max_rows=100,
    )

    assert "LIMIT 100" in sql.upper()
