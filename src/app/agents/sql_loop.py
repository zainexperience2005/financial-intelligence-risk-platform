from dataclasses import dataclass, field


@dataclass
class SQLLoopState:
    iterations: int = 0
    sql_attempts: int = 0
    failed_sql_attempts: int = 0

    executed_queries: list[str] = field(default_factory=list)

    last_error: str | None = None

    @property
    def successful(self) -> bool:
        return self.sql_attempts > 0 and self.last_error is None
