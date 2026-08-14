"""SQL Executor: runs pre-validated SQL under strict, defense-in-depth safety limits.

Even though the SQL Validator already rejects write statements, the executor
independently enforces a read-only transaction, a statement timeout, and a
hard row cap — validated SQL from an LLM is still untrusted input.
"""
from dataclasses import dataclass, field

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError


@dataclass
class SQLExecutionResult:
    success: bool
    columns: list[str] = field(default_factory=list)
    rows: list[dict] = field(default_factory=list)
    row_count: int = 0
    truncated: bool = False
    error: str | None = None


def execute_sql(
    engine: Engine, sql: str, max_rows: int, timeout_seconds: int
) -> SQLExecutionResult:
    """Executes `sql` (assumed already validated as a single read-only SELECT)
    and returns at most `max_rows` rows, aborting after `timeout_seconds`.
    """
    bounded_sql = f"SELECT * FROM ({sql.rstrip(';')}) AS bounded_query LIMIT :__max_rows_plus_one"

    try:
        with engine.connect() as conn:
            with conn.begin():
                conn.execute(text("SET TRANSACTION READ ONLY"))
                conn.execute(text(f"SET LOCAL statement_timeout = {int(timeout_seconds * 1000)}"))
                result = conn.execute(text(bounded_sql), {"__max_rows_plus_one": max_rows + 1})
                columns = list(result.keys())
                rows = [dict(zip(columns, row, strict=True)) for row in result.fetchall()]
    except DBAPIError as e:
        return SQLExecutionResult(success=False, error=str(e.orig) if e.orig else str(e))

    truncated = len(rows) > max_rows
    if truncated:
        rows = rows[:max_rows]

    return SQLExecutionResult(
        success=True, columns=columns, rows=rows, row_count=len(rows), truncated=truncated
    )
