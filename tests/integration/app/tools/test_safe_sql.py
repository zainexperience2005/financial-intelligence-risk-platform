from kit.databases.sql import apply_row_limit
from kit.databases.sql import validate_read_only_sql
from app.tools import (
    SafeSQLInput,
    SafeSQLTool,
)


def test_safe_sql_executes_select() -> None:
    tool = SafeSQLTool()

    result = tool.execute(
        SafeSQLInput(
            query="""
            SELECT transaction_id, status
            FROM transactions
            """
        )
    )

    assert result.success is True
    assert result.data["row_count"] > 0


def test_safe_sql_rejects_delete() -> None:
    tool = SafeSQLTool()

    result = tool.execute(
        SafeSQLInput(
            query="DELETE FROM transactions"
        )
    )

    assert result.success is False



def test_large_limit_is_reduced() -> None:
    statement = validate_read_only_sql(
        """
        SELECT *
        FROM transactions
        LIMIT 1000000
        """
    )

    sql = apply_row_limit(
        statement,
        max_rows=100,
    )

    assert "LIMIT 100" in sql.upper()