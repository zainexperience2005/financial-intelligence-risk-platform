from sqlalchemy.exc import ProgrammingError


def classify_sql_error(
    exc: Exception,
) -> str:
    if isinstance(exc, ProgrammingError):
        message = str(exc.orig).lower()

        if "column" in message and "does not exist" in message:
            return "Query references a column that does not exist."

        if "relation" in message and "does not exist" in message:
            return "Query references a table that does not exist."

        return "The SQL query is invalid for the current schema."

    return "SQL execution failed."
