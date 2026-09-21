from app.agents.sql_loop import SQLLoopState


def test_new_loop_state() -> None:
    state = SQLLoopState()

    assert state.iterations == 0
    assert state.sql_attempts == 0
    assert state.failed_sql_attempts == 0
    assert state.executed_queries == []


def test_query_tracking() -> None:
    state = SQLLoopState()

    query = "SELECT * FROM transactions"

    state.sql_attempts += 1
    state.executed_queries.append(query)

    assert state.sql_attempts == 1

    assert state.executed_queries.count(query) == 1


def test_failed_attempt_tracking() -> None:
    state = SQLLoopState()

    state.sql_attempts += 1
    state.failed_sql_attempts += 1
    state.last_error = "Column does not exist."

    assert state.failed_sql_attempts == 1
    assert state.successful is False


def test_successful_state() -> None:
    state = SQLLoopState()

    state.sql_attempts = 2
    state.failed_sql_attempts = 1
    state.last_error = None

    assert state.successful is True
