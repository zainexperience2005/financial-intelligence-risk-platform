import sqlglot
from sqlglot import exp

from kit.databases.sql.errors import SQLValidationError


FORBIDDEN_EXPRESSIONS = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Create,
    exp.Alter,
)


def validate_read_only_sql(
    sql: str,
) -> exp.Expression:
    try:
        statements = sqlglot.parse(
            sql,
            read="postgres",
        )
    except sqlglot.errors.ParseError as exc:
        raise SQLValidationError(
            "SQL could not be parsed."
        ) from exc

    if len(statements) != 1:
        raise SQLValidationError(
            "Exactly one SQL statement is allowed."
        )

    statement = statements[0]

    if statement is None:
        raise SQLValidationError(
            "SQL statement is empty."
        )

    for expression_type in FORBIDDEN_EXPRESSIONS:
        if statement.find(expression_type):
            raise SQLValidationError(
                "Only read-only SQL is allowed."
            )

    if not isinstance(
        statement,
        (exp.Select, exp.Union),
    ):
        raise SQLValidationError(
            "Only SELECT queries are allowed."
        )

    return statement


def apply_row_limit(
    statement: exp.Expression,
    max_rows: int = 100,
) -> str:
    limit = statement.args.get("limit")

    if limit is None:
        statement = statement.limit(max_rows)

    else:
        limit_expression = limit.expression

        if isinstance(
            limit_expression,
            exp.Literal,
        ):
            requested = int(
                limit_expression.this
            )

            if requested > max_rows:
                statement = statement.limit(
                    max_rows
                )

    return statement.sql(
        dialect="postgres"
    )